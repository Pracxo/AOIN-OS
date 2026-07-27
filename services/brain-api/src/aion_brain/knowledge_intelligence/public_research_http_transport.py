"""Pinned HTTPS transport boundary for the AION-219 public research pilot."""

from __future__ import annotations

import http.client
import ipaddress
import socket as net
import ssl
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol
from urllib.parse import urlsplit

from aion_brain.contracts.knowledge_public_research_pilot import (
    PublicResearchHttpExchangeMetadata,
    PublicResearchHttpOutcome,
    PublicResearchPinnedDestination,
    body_digest,
    public_research_fingerprint,
)
from aion_brain.knowledge_intelligence.public_research_dns import (
    PublicResearchDnsError,
    peer_fingerprint,
)
from aion_brain.knowledge_intelligence.public_research_policy import (
    REDIRECT_STATUSES,
    RequestMethod,
    canonicalize_public_research_url,
    fixed_request_headers,
    host_header_for_url,
    request_target_for_url,
    response_policy_decision,
    validate_response_body_size,
)
from aion_brain.knowledge_intelligence.public_research_session import (
    PublicResearchPilotKillSwitch,
)

READ_CHUNK_SIZE = 64 * 1024


class PublicResearchTransportError(RuntimeError):
    """Raised when the pinned transport fails closed."""

    def __init__(self, outcome: PublicResearchHttpOutcome, reason_code: str) -> None:
        super().__init__(reason_code)
        self.outcome = outcome
        self.reason_code = reason_code


@dataclass(frozen=True)
class InMemoryHttpsFixture:
    """Deterministic HTTPS fixture for offline tests."""

    method: RequestMethod
    url: str
    status_code: int = 200
    headers: tuple[tuple[str, str], ...] = (("Content-Type", "text/plain; charset=utf-8"),)
    body: bytes = b""
    peer_address: str = "93.184.216.34"
    tls_protocol_version: str = "TLSv1.3"
    certificate_subject: str = "fixture subject"
    certificate_issuer: str = "fixture issuer"
    certificate_valid: bool = True
    hostname_valid: bool = True
    timeout: bool = False

    @property
    def canonical_url(self) -> str:
        """Return the canonical fixture URL."""

        return canonicalize_public_research_url(self.url)


@dataclass
class PublicResearchTransportResponse:
    """Ephemeral response object; body must be purged by the pilot."""

    exchange_metadata: PublicResearchHttpExchangeMetadata
    final_url: str
    status_code: int
    raw_headers: tuple[tuple[str, str], ...]
    body: bytes
    body_purged: bool = False

    def purge_body(self) -> None:
        """Release the source body reference from this response."""

        self.body = b""
        self.body_purged = True


class PublicResearchConnectionBackend(Protocol):
    """Protocol for explicit pinned HTTPS backends."""

    system_http_transport_available: bool

    def fetch(
        self,
        *,
        method: RequestMethod,
        url: str,
        destination: PublicResearchPinnedDestination,
        request_id: str,
        exchange_id: str,
        maximum_response_bytes: int,
        maximum_total_transfer_bytes: int,
        current_total_transfer_bytes: int,
        timeout_seconds: int,
        allowed_content_types: tuple[str, ...],
        started_at: datetime,
        kill_switch: PublicResearchPilotKillSwitch,
    ) -> PublicResearchTransportResponse:
        """Fetch exactly one URL through an explicit pinned destination."""


class DisabledPublicResearchConnectionBackend:
    """Default fail-closed connection backend."""

    system_http_transport_available = False

    def fetch(
        self,
        *,
        method: RequestMethod,
        url: str,
        destination: PublicResearchPinnedDestination,
        request_id: str,
        exchange_id: str,
        maximum_response_bytes: int,
        maximum_total_transfer_bytes: int,
        current_total_transfer_bytes: int,
        timeout_seconds: int,
        allowed_content_types: tuple[str, ...],
        started_at: datetime,
        kill_switch: PublicResearchPilotKillSwitch,
    ) -> PublicResearchTransportResponse:
        del (
            method,
            url,
            destination,
            request_id,
            exchange_id,
            maximum_response_bytes,
            maximum_total_transfer_bytes,
            current_total_transfer_bytes,
            timeout_seconds,
            allowed_content_types,
            started_at,
            kill_switch,
        )
        raise PublicResearchTransportError(
            PublicResearchHttpOutcome.FAILED,
            "public_research_connection_backend_disabled",
        )


class InMemoryPinnedHttpsBackend:
    """Deterministic pinned HTTPS backend for CI and local tests."""

    system_http_transport_available = False

    def __init__(
        self,
        fixtures: Mapping[tuple[RequestMethod, str], InMemoryHttpsFixture],
        *,
        completed_at: datetime,
    ) -> None:
        self._fixtures = {
            (method, canonicalize_public_research_url(url)): fixture
            for (method, url), fixture in fixtures.items()
        }
        self._completed_at = completed_at

    def fetch(
        self,
        *,
        method: RequestMethod,
        url: str,
        destination: PublicResearchPinnedDestination,
        request_id: str,
        exchange_id: str,
        maximum_response_bytes: int,
        maximum_total_transfer_bytes: int,
        current_total_transfer_bytes: int,
        timeout_seconds: int,
        allowed_content_types: tuple[str, ...],
        started_at: datetime,
        kill_switch: PublicResearchPilotKillSwitch,
    ) -> PublicResearchTransportResponse:
        del timeout_seconds
        kill_switch.raise_if_triggered("before_fixture_fetch")
        canonical_url = canonicalize_public_research_url(url)
        key = (method, canonical_url)
        fixture = self._fixtures.get(key)
        if fixture is None:
            raise PublicResearchTransportError(
                PublicResearchHttpOutcome.FAILED,
                "https_fixture_unavailable",
            )
        if fixture.timeout:
            raise PublicResearchTransportError(PublicResearchHttpOutcome.TIMEOUT, "timeout")
        if not fixture.certificate_valid:
            raise PublicResearchTransportError(
                PublicResearchHttpOutcome.REJECTED_TLS,
                "certificate_verification_failed",
            )
        if not fixture.hostname_valid:
            raise PublicResearchTransportError(
                PublicResearchHttpOutcome.REJECTED_TLS,
                "hostname_verification_failed",
            )
        try:
            peer_fp = peer_fingerprint(fixture.peer_address, destination)
        except PublicResearchDnsError as exc:
            raise PublicResearchTransportError(
                PublicResearchHttpOutcome.REJECTED_PEER,
                "peer_address_not_pinned",
            ) from exc
        body = b"" if method == "HEAD" else fixture.body
        policy = response_policy_decision(
            status_code=fixture.status_code,
            method=method,
            headers=fixture.headers,
            maximum_response_bytes=maximum_response_bytes,
            allowed_content_types=allowed_content_types,
        )
        validate_response_body_size(
            len(body),
            maximum_response_bytes=maximum_response_bytes,
            total_transfer_bytes=current_total_transfer_bytes,
            maximum_total_transfer_bytes=maximum_total_transfer_bytes,
        )
        outcome = (
            PublicResearchHttpOutcome.REDIRECTED
            if fixture.status_code in REDIRECT_STATUSES
            else PublicResearchHttpOutcome.COMPLETED
        )
        return PublicResearchTransportResponse(
            exchange_metadata=_exchange_metadata(
                exchange_id=exchange_id,
                request_id=request_id,
                method=method,
                url=canonical_url,
                destination=destination,
                peer_address_fingerprint=peer_fp,
                tls_protocol_version=fixture.tls_protocol_version,
                certificate_subject=fixture.certificate_subject,
                certificate_issuer=fixture.certificate_issuer,
                status_code=fixture.status_code,
                safe_response_header_fingerprint=policy.safe_header_fingerprint,
                content_type=policy.content_type,
                character_encoding=policy.character_encoding,
                body=body,
                redirect_count=0,
                started_at=started_at,
                completed_at=self._completed_at,
                outcome=outcome,
            ),
            final_url=canonical_url,
            status_code=fixture.status_code,
            raw_headers=fixture.headers,
            body=body,
        )


class SystemPinnedHttpsBackend:
    """Live operator-invoked pinned HTTPS backend."""

    system_http_transport_available = True

    def fetch(
        self,
        *,
        method: RequestMethod,
        url: str,
        destination: PublicResearchPinnedDestination,
        request_id: str,
        exchange_id: str,
        maximum_response_bytes: int,
        maximum_total_transfer_bytes: int,
        current_total_transfer_bytes: int,
        timeout_seconds: int,
        allowed_content_types: tuple[str, ...],
        started_at: datetime,
        kill_switch: PublicResearchPilotKillSwitch,
    ) -> PublicResearchTransportResponse:
        canonical_url = canonicalize_public_research_url(url)
        split = urlsplit(canonical_url)
        if split.hostname != destination.hostname:
            raise PublicResearchTransportError(
                PublicResearchHttpOutcome.REJECTED_DESTINATION,
                "destination_hostname_mismatch",
            )
        address = _select_pinned_address(destination)
        family = _tcp_family_for_address(address)
        raw_stream: net.socket | None = None
        tls_stream: ssl.SSLSocket | None = None
        try:
            kill_switch.raise_if_triggered("before_socket_create")
            raw_stream = net.socket(family, net.SOCK_STREAM)
            raw_stream.settimeout(timeout_seconds)
            kill_switch.raise_if_triggered("before_socket_connect")
            raw_stream.connect((address, destination.port))
            context = _verified_ssl_context()
            kill_switch.raise_if_triggered("before_tls_handshake")
            tls_stream = context.wrap_socket(raw_stream, server_hostname=destination.hostname)
            raw_stream = None
            peer = str(tls_stream.getpeername()[0])
            try:
                peer_fp = peer_fingerprint(peer, destination)
            except PublicResearchDnsError as exc:
                raise PublicResearchTransportError(
                    PublicResearchHttpOutcome.REJECTED_PEER,
                    "peer_address_not_pinned",
                ) from exc
            kill_switch.raise_if_triggered("before_request_send")
            request_bytes = _build_request_bytes(
                method=method,
                url=canonical_url,
                allowed_content_types=allowed_content_types,
            )
            tls_stream.sendall(request_bytes)
            response = http.client.HTTPResponse(tls_stream, method=method)
            response.begin()
            headers = tuple((str(name), str(value)) for name, value in response.getheaders())
            policy = response_policy_decision(
                status_code=response.status,
                method=method,
                headers=headers,
                maximum_response_bytes=maximum_response_bytes,
                allowed_content_types=allowed_content_types,
            )
            body = b""
            if method != "HEAD" and response.status not in REDIRECT_STATUSES:
                body = _read_bounded_body(
                    response,
                    maximum_response_bytes=maximum_response_bytes,
                    maximum_total_transfer_bytes=maximum_total_transfer_bytes,
                    current_total_transfer_bytes=current_total_transfer_bytes,
                    kill_switch=kill_switch,
                )
            validate_response_body_size(
                len(body),
                maximum_response_bytes=maximum_response_bytes,
                total_transfer_bytes=current_total_transfer_bytes,
                maximum_total_transfer_bytes=maximum_total_transfer_bytes,
            )
            outcome = (
                PublicResearchHttpOutcome.REDIRECTED
                if response.status in REDIRECT_STATUSES
                else PublicResearchHttpOutcome.COMPLETED
            )
            certificate = tls_stream.getpeercert() or {}
            completed_at = started_at if started_at.tzinfo is None else started_at
            return PublicResearchTransportResponse(
                exchange_metadata=_exchange_metadata(
                    exchange_id=exchange_id,
                    request_id=request_id,
                    method=method,
                    url=canonical_url,
                    destination=destination,
                    peer_address_fingerprint=peer_fp,
                    tls_protocol_version=tls_stream.version() or "TLS",
                    certificate_subject=public_research_fingerprint(
                        certificate.get("subject", ())
                    ),
                    certificate_issuer=public_research_fingerprint(
                        certificate.get("issuer", ())
                    ),
                    status_code=response.status,
                    safe_response_header_fingerprint=policy.safe_header_fingerprint,
                    content_type=policy.content_type,
                    character_encoding=policy.character_encoding,
                    body=body,
                    redirect_count=0,
                    started_at=started_at,
                    completed_at=completed_at,
                    outcome=outcome,
                ),
                final_url=canonical_url,
                status_code=response.status,
                raw_headers=headers,
                body=body,
            )
        except TimeoutError as exc:
            raise PublicResearchTransportError(
                PublicResearchHttpOutcome.TIMEOUT,
                "timeout",
            ) from exc
        except ssl.SSLError as exc:
            raise PublicResearchTransportError(
                PublicResearchHttpOutcome.REJECTED_TLS,
                "tls_verification_failed",
            ) from exc
        except OSError as exc:
            raise PublicResearchTransportError(
                PublicResearchHttpOutcome.FAILED,
                "socket_failed",
            ) from exc
        finally:
            if tls_stream is not None:
                tls_stream.close()
            if raw_stream is not None:
                raw_stream.close()


def _verified_ssl_context() -> ssl.SSLContext:
    context = ssl.create_default_context()
    context.check_hostname = True
    context.verify_mode = ssl.CERT_REQUIRED
    context.minimum_version = ssl.TLSVersion.TLSv1_2
    context.options |= ssl.OP_NO_COMPRESSION
    if hasattr(context, "keylog_filename"):
        context.keylog_filename = None  # type: ignore[assignment]
    return context


def _build_request_bytes(
    *,
    method: RequestMethod,
    url: str,
    allowed_content_types: tuple[str, ...],
) -> bytes:
    headers = fixed_request_headers(allowed_content_types)
    headers["Host"] = host_header_for_url(url)
    lines = [f"{method} {request_target_for_url(url)} HTTP/1.1"]
    lines.extend(f"{name}: {value}" for name, value in sorted(headers.items()))
    return ("\r\n".join(lines) + "\r\n\r\n").encode("ascii")


def _read_bounded_body(
    response: http.client.HTTPResponse,
    *,
    maximum_response_bytes: int,
    maximum_total_transfer_bytes: int,
    current_total_transfer_bytes: int,
    kill_switch: PublicResearchPilotKillSwitch,
) -> bytes:
    chunks: list[bytes] = []
    total = 0
    while True:
        kill_switch.raise_if_triggered("before_response_chunk")
        chunk = response.read(READ_CHUNK_SIZE)
        if not chunk:
            break
        total += len(chunk)
        validate_response_body_size(
            total,
            maximum_response_bytes=maximum_response_bytes,
            total_transfer_bytes=current_total_transfer_bytes,
            maximum_total_transfer_bytes=maximum_total_transfer_bytes,
        )
        chunks.append(chunk)
    return b"".join(chunks)


def _select_pinned_address(destination: PublicResearchPinnedDestination) -> str:
    if not destination.address_family_by_address:
        raise PublicResearchTransportError(
            PublicResearchHttpOutcome.REJECTED_DESTINATION,
            "pinned_destination_empty",
        )
    return sorted(destination.address_family_by_address)[0]


def _tcp_family_for_address(address: str) -> net.AddressFamily:
    parsed = ipaddress.ip_address(address)
    return net.AF_INET if parsed.version == 4 else net.AF_INET6


def _exchange_metadata(
    *,
    exchange_id: str,
    request_id: str,
    method: RequestMethod,
    url: str,
    destination: PublicResearchPinnedDestination,
    peer_address_fingerprint: str,
    tls_protocol_version: str,
    certificate_subject: str,
    certificate_issuer: str,
    status_code: int,
    safe_response_header_fingerprint: str,
    content_type: str,
    character_encoding: str | None,
    body: bytes,
    redirect_count: int,
    started_at: datetime,
    completed_at: datetime,
    outcome: PublicResearchHttpOutcome,
) -> PublicResearchHttpExchangeMetadata:
    payload = {
        "exchange_id": exchange_id,
        "request_id": request_id,
        "url": public_research_fingerprint({"url": url}),
        "destination": destination.resolution.resolution_fingerprint,
        "status_code": status_code,
        "body_sha256": body_digest(body),
        "outcome": outcome.value,
    }
    return PublicResearchHttpExchangeMetadata(
        exchange_id=exchange_id,
        request_id=request_id,
        method=method,
        canonical_url_fingerprint=public_research_fingerprint({"url": url}),
        hostname_fingerprint=public_research_fingerprint({"hostname": destination.hostname}),
        destination_resolution_fingerprint=destination.resolution.resolution_fingerprint,
        peer_address_fingerprint=peer_address_fingerprint,
        tls_protocol_version=tls_protocol_version,
        certificate_subject_fingerprint=public_research_fingerprint(
            {"certificate_subject": certificate_subject}
        ),
        certificate_issuer_fingerprint=public_research_fingerprint(
            {"certificate_issuer": certificate_issuer}
        ),
        status_code=status_code,
        safe_response_header_fingerprint=safe_response_header_fingerprint,
        content_type=content_type,
        character_encoding=character_encoding,
        body_length=len(body),
        body_sha256=body_digest(body),
        redirect_count=redirect_count,
        started_at=started_at,
        completed_at=completed_at,
        outcome=outcome,
        exchange_fingerprint=public_research_fingerprint(payload),
    )


__all__ = [
    "DisabledPublicResearchConnectionBackend",
    "InMemoryHttpsFixture",
    "InMemoryPinnedHttpsBackend",
    "PublicResearchConnectionBackend",
    "PublicResearchTransportError",
    "PublicResearchTransportResponse",
    "SystemPinnedHttpsBackend",
]
