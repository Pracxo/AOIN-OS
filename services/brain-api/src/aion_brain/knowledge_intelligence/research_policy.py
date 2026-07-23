"""Pure policy helpers for controlled research acquisition."""

from __future__ import annotations

import ipaddress
import posixpath
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol, Self
from urllib.parse import unquote, urlsplit, urlunsplit

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from aion_brain.contracts.knowledge_research import (
    MAXIMUM_DOMAINS_PER_PLAN,
    MAXIMUM_REDIRECTS_PER_FETCH,
    MAXIMUM_SAFE_HEADERS_PER_SNAPSHOT,
    ResearchContentType,
    ResearchMethod,
    ensure_utc,
    fingerprint_payload,
    reject_protected_material,
    sha256_bytes,
    validate_hex64,
)

_MALFORMED_PERCENT_RE = re.compile(r"%(?![0-9A-Fa-f]{2})")
_CONTROL_OR_SPACE_RE = re.compile(r"[\x00-\x20\x7f]")
_IP_LITERAL_RE = re.compile(r"^\[?[0-9a-fA-F:.]+\]?$")
_ODD_IPV4_RE = re.compile(r"^(0x[0-9a-fA-F]+|0[0-7]+|\d+)([.](0x[0-9a-fA-F]+|0[0-7]+|\d+))*$")
_PROMPT_MARKERS = (
    "ignore previous instructions",
    "ignore all previous instructions",
    "system prompt",
    "developer prompt",
    "tool call",
    "execute this",
    "run this command",
    "create a pull request",
    "merge this",
    "mark this as verified",
    "promote this into memory",
)
_ALLOWED_CONTENT_TYPES = {
    "text/html",
    "text/plain",
    "application/json",
    "application/pdf",
    "application/xml",
    "text/xml",
}
_ALLOWED_ENCODINGS = {"utf-8", "utf-8-sig", "us-ascii", "iso-8859-1", "windows-1252"}
_SAFE_RESPONSE_HEADERS = {
    "content-type": "Content-Type",
    "content-length": "Content-Length",
    "content-language": "Content-Language",
    "date": "Date",
    "last-modified": "Last-Modified",
    "etag": "ETag",
    "cache-control": "Cache-Control",
    "expires": "Expires",
    "link": "Link",
    "x-robots-tag": "X-Robots-Tag",
}
_UNSAFE_RESPONSE_HEADERS = {
    "set-cookie",
    "www-authenticate",
    "proxy-authenticate",
    "authorization",
    "x-request-id",
    "x-trace-id",
    "x-amzn-trace-id",
}
_DEFAULT_HTTPS_PORT = 443
_METADATA_ADDRESSES = {
    ipaddress.ip_address("169.254.169.254"),
    ipaddress.ip_address("100.100.100.200"),
}
_DOCUMENTATION_NETS = (
    ipaddress.ip_network("192.0.2.0/24"),
    ipaddress.ip_network("198.51.100.0/24"),
    ipaddress.ip_network("203.0.113.0/24"),
    ipaddress.ip_network("2001:db8::/32"),
)


class CanonicalResearchUrl(BaseModel):
    """Canonical URL representation used for policy decisions."""

    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True, frozen=True)

    scheme: str
    hostname: str
    port: int
    path: str
    query: str
    canonical_url: str
    original_url_fingerprint: str
    canonical_url_fingerprint: str

    @field_validator("original_url_fingerprint", "canonical_url_fingerprint")
    @classmethod
    def fingerprints_are_hex(cls, value: str) -> str:
        return validate_hex64(value, "url fingerprint")


class DomainAllowlistPolicy(BaseModel):
    """Explicit host and wildcard allowlist with deterministic fingerprint."""

    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True, frozen=True)

    exact_hosts: tuple[str, ...] = Field(default_factory=tuple, max_length=20)
    wildcard_hosts: tuple[str, ...] = Field(default_factory=tuple, max_length=20)
    allowed_ports: tuple[int, ...] = Field(default=(_DEFAULT_HTTPS_PORT,), min_length=1)
    allow_subdomains: bool = True
    fingerprint: str

    @field_validator("exact_hosts", "wildcard_hosts")
    @classmethod
    def hosts_are_safe(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        if len(set(values)) != len(values):
            raise ValueError("duplicate allowlist hosts are rejected")
        return tuple(_normalize_policy_host(value) for value in values)

    @field_validator("allowed_ports")
    @classmethod
    def ports_are_safe(cls, values: tuple[int, ...]) -> tuple[int, ...]:
        if len(set(values)) != len(values):
            raise ValueError("duplicate ports are rejected")
        for port in values:
            if port < 1 or port > 65535:
                raise ValueError("port is outside policy bounds")
        return tuple(sorted(values))

    @field_validator("fingerprint")
    @classmethod
    def fingerprint_is_hex(cls, value: str) -> str:
        return validate_hex64(value, "allowlist fingerprint")

    @model_validator(mode="after")
    def allowlist_is_valid(self) -> Self:
        if len(self.exact_hosts) + len(self.wildcard_hosts) > MAXIMUM_DOMAINS_PER_PLAN:
            raise ValueError("too many allowlist domains")
        for host in self.wildcard_hosts:
            if not host.startswith("*."):
                raise ValueError("wildcard host must start with *.")
            root = host[2:]
            if not root or "." not in root:
                raise ValueError("wildcard host must not target a public suffix")
            if root in self.exact_hosts:
                continue
        return self


class ResolvedResearchDestination(BaseModel):
    """Pinned synthetic destination resolution result."""

    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True, frozen=True)

    hostname: str
    resolved_addresses: tuple[str, ...]
    validated_public_addresses: tuple[str, ...]
    resolution_fingerprint: str
    resolved_at: datetime

    @field_validator("resolved_addresses", "validated_public_addresses")
    @classmethod
    def addresses_are_unique(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        if len(set(values)) != len(values):
            raise ValueError("duplicate destination addresses are rejected")
        return tuple(sorted(values))

    @field_validator("resolution_fingerprint")
    @classmethod
    def resolution_fingerprint_is_hex(cls, value: str) -> str:
        return validate_hex64(value, "resolution fingerprint")

    @field_validator("resolved_at")
    @classmethod
    def resolved_at_is_utc(cls, value: datetime) -> datetime:
        return ensure_utc(value, "resolved_at")


class ResearchDestinationResolver(Protocol):
    """Protocol for explicit destination resolvers."""

    def resolve(self, hostname: str, port: int) -> ResolvedResearchDestination:
        """Resolve a host using an explicit policy-controlled resolver."""


@dataclass(frozen=True)
class InMemoryResearchDestinationResolver:
    """Immutable no-network host-to-address resolver."""

    host_addresses: dict[str, tuple[str, ...]]
    resolved_at: datetime

    def resolve(self, hostname: str, port: int) -> ResolvedResearchDestination:
        normalized = _normalize_policy_host(hostname)
        if normalized not in self.host_addresses:
            raise ValueError("destination host is not registered")
        raw_addresses = self.host_addresses[normalized]
        if len(set(raw_addresses)) != len(raw_addresses):
            raise ValueError("duplicate destination address fixture")
        validated = tuple(validate_public_destination_address(item) for item in raw_addresses)
        payload = {
            "hostname": normalized,
            "port": port,
            "addresses": sorted(validated),
            "resolved_at": self.resolved_at.isoformat(),
        }
        return ResolvedResearchDestination(
            hostname=normalized,
            resolved_addresses=tuple(sorted(raw_addresses)),
            validated_public_addresses=tuple(sorted(validated)),
            resolution_fingerprint=fingerprint_payload(payload),
            resolved_at=self.resolved_at,
        )


def canonicalize_research_url(
    url: str,
    *,
    allow_http_fixture: bool = False,
) -> CanonicalResearchUrl:
    """Canonicalize a research URL without broadening request semantics."""

    if len(url) > 4096:
        raise ValueError("URL exceeds maximum length")
    if "\\" in url or _CONTROL_OR_SPACE_RE.search(url):
        raise ValueError("URL contains prohibited characters")
    if _MALFORMED_PERCENT_RE.search(url):
        raise ValueError("URL contains malformed percent encoding")
    split = urlsplit(url)
    scheme = split.scheme.lower()
    if scheme not in {"https", "http"}:
        raise ValueError("URL scheme is not allowed")
    if scheme == "http" and not allow_http_fixture:
        raise ValueError("public HTTP is prohibited")
    if split.username or split.password:
        raise ValueError("URL userinfo is rejected")
    if split.fragment:
        split = split._replace(fragment="")
    if not split.hostname:
        raise ValueError("URL hostname is required")
    hostname = _normalize_policy_host(split.hostname)
    if _looks_like_ip_literal(hostname):
        raise ValueError("direct IP literals are rejected")
    if split.port is not None and (split.port < 1 or split.port > 65535):
        raise ValueError("port is outside policy bounds")
    port = split.port or (_DEFAULT_HTTPS_PORT if scheme == "https" else 80)
    raw_path = split.path or "/"
    if _path_traverses(raw_path):
        raise ValueError("path traversal is rejected")
    path = _normalize_path(raw_path)
    query = _normalize_unreserved_percent(split.query)
    netloc = hostname if port == _DEFAULT_HTTPS_PORT and scheme == "https" else f"{hostname}:{port}"
    canonical_url = urlunsplit((scheme, netloc, path, query, ""))
    return CanonicalResearchUrl(
        scheme=scheme,
        hostname=hostname,
        port=port,
        path=path,
        query=query,
        canonical_url=canonical_url,
        original_url_fingerprint=sha256_bytes(url.encode("utf-8")),
        canonical_url_fingerprint=sha256_bytes(canonical_url.encode("utf-8")),
    )


def validate_domain_allowlist(
    exact_hosts: tuple[str, ...],
    wildcard_hosts: tuple[str, ...] = (),
    *,
    allowed_ports: tuple[int, ...] = (_DEFAULT_HTTPS_PORT,),
) -> DomainAllowlistPolicy:
    """Return a deterministic allowlist policy."""

    normalized_exact = tuple(sorted(_normalize_policy_host(host) for host in exact_hosts))
    normalized_wildcards = tuple(sorted(_normalize_wildcard_host(host) for host in wildcard_hosts))
    ports = tuple(sorted(allowed_ports))
    fingerprint = fingerprint_payload(
        {"exact_hosts": normalized_exact, "wildcard_hosts": normalized_wildcards, "ports": ports}
    )
    return DomainAllowlistPolicy(
        exact_hosts=normalized_exact,
        wildcard_hosts=normalized_wildcards,
        allowed_ports=ports,
        fingerprint=fingerprint,
    )


def host_is_allowlisted(hostname: str, port: int, policy: DomainAllowlistPolicy) -> bool:
    """Return whether a normalized host and port match the explicit policy."""

    host = _normalize_policy_host(hostname)
    if port not in policy.allowed_ports:
        return False
    if host in policy.exact_hosts:
        return True
    if not policy.allow_subdomains:
        return False
    for wildcard in policy.wildcard_hosts:
        root = wildcard[2:]
        if host.endswith(f".{root}") and host != root:
            return True
    return False


def validate_public_destination_address(address: str) -> str:
    """Reject private, local, metadata, ambiguous, and malformed destinations."""

    if _is_ambiguous_ipv4_text(address):
        raise ValueError("ambiguous IPv4 encoding is rejected")
    try:
        parsed = ipaddress.ip_address(address)
    except ValueError as exc:
        raise ValueError("malformed destination address") from exc
    if parsed in _METADATA_ADDRESSES:
        raise ValueError("metadata service address is rejected")
    if isinstance(parsed, ipaddress.IPv6Address) and parsed.ipv4_mapped is not None:
        validate_public_destination_address(str(parsed.ipv4_mapped))
    if parsed.is_private:
        raise ValueError("private destination address is rejected")
    if parsed.is_loopback:
        raise ValueError("loopback destination address is rejected")
    if parsed.is_link_local:
        raise ValueError("link-local destination address is rejected")
    if parsed.is_multicast:
        raise ValueError("multicast destination address is rejected")
    if parsed.is_reserved:
        raise ValueError("reserved destination address is rejected")
    if parsed.is_unspecified:
        raise ValueError("unspecified destination address is rejected")
    if any(parsed in network for network in _DOCUMENTATION_NETS):
        raise ValueError("documentation destination address is rejected")
    return str(parsed)


def validate_peer_matches_destination(
    peer_address: str,
    destination: ResolvedResearchDestination,
) -> None:
    """Ensure the transport peer address matches the pinned validated address."""

    normalized = validate_public_destination_address(peer_address)
    if normalized not in destination.validated_public_addresses:
        raise ValueError("peer destination mismatch")


def project_safe_request_headers(content_types: tuple[ResearchContentType, ...]) -> dict[str, str]:
    """Create fixed non-secret outbound headers."""

    accept = ", ".join(content_types)
    return {
        "User-Agent": "AION-Knowledge-Research/disabled-operator-invoked",
        "Accept": accept,
        "Accept-Language": "en",
        "Accept-Encoding": "identity",
    }


def project_safe_response_headers(headers: dict[str, str]) -> dict[str, str]:
    """Retain only bounded safe response headers."""

    projected: dict[str, str] = {}
    for key in sorted(headers):
        lowered = key.lower()
        if lowered in _UNSAFE_RESPONSE_HEADERS or lowered not in _SAFE_RESPONSE_HEADERS:
            continue
        value = headers[key]
        if "\r" in key or "\n" in key or "\r" in value or "\n" in value:
            raise ValueError("header newline injection is rejected")
        reject_protected_material(value, "safe response header")
        projected[_SAFE_RESPONSE_HEADERS[lowered]] = value[:512]
        if len(projected) > MAXIMUM_SAFE_HEADERS_PER_SNAPSHOT:
            raise ValueError("too many safe response headers")
    return projected


def parse_and_validate_content_type(raw_value: str) -> ResearchContentType:
    """Validate a declared content type without sniffing to broaden it."""

    media_type = raw_value.split(";", 1)[0].strip().lower()
    if media_type not in _ALLOWED_CONTENT_TYPES:
        raise ValueError("content type is not allowed")
    return media_type  # type: ignore[return-value]


def validate_character_encoding(
    content_type: ResearchContentType,
    encoding: str | None,
) -> str | None:
    """Validate explicit character encodings for text-like content."""

    if content_type == "application/pdf":
        return None
    effective = (encoding or ("utf-8" if content_type == "application/json" else "")).lower()
    if effective not in _ALLOWED_ENCODINGS:
        raise ValueError("character encoding is not allowed")
    return effective


def decode_research_text(body: bytes, encoding: str) -> str:
    """Decode bytes strictly with an approved character encoding."""

    return body.decode(encoding, errors="strict")


def redirect_method_after(status_code: int, method: ResearchMethod) -> ResearchMethod:
    """Return the next read-only method after a redirect."""

    if status_code not in {301, 302, 303, 307, 308}:
        raise ValueError("status code is not a redirect")
    return method


def validate_redirect_chain(chain: tuple[str, ...]) -> str:
    """Validate redirect loop and length policy and return a fingerprint."""

    if len(chain) > MAXIMUM_REDIRECTS_PER_FETCH:
        raise ValueError("redirect limit exceeded")
    if len(set(chain)) != len(chain):
        raise ValueError("redirect loop detected")
    return fingerprint_payload({"redirect_chain": chain})


def detect_untrusted_content_instruction_markers(content: str | bytes) -> tuple[str, ...]:
    """Detect instruction-like markers in untrusted acquired content."""

    text = content.decode("utf-8", errors="ignore") if isinstance(content, bytes) else content
    lowered = text.lower()
    return tuple(marker for marker in _PROMPT_MARKERS if marker in lowered)


def _normalize_policy_host(hostname: str) -> str:
    host = hostname.strip().rstrip(".")
    if not host or host in {"*", "*.*"}:
        raise ValueError("universal wildcard is rejected")
    if "\x00" in host:
        raise ValueError("NUL host is rejected")
    if _looks_like_ip_literal(host):
        raise ValueError("direct IP literals are rejected")
    return host.encode("idna").decode("ascii").lower()


def _normalize_wildcard_host(hostname: str) -> str:
    host = hostname.strip().rstrip(".")
    if not host.startswith("*."):
        raise ValueError("wildcard host must start with *.")
    root = _normalize_policy_host(host[2:])
    if "." not in root:
        raise ValueError("wildcard host must not target a public suffix")
    return f"*.{root}"


def _looks_like_ip_literal(hostname: str) -> bool:
    if _IP_LITERAL_RE.fullmatch(hostname):
        try:
            ipaddress.ip_address(hostname.strip("[]"))
            return True
        except ValueError:
            return False
    return _ODD_IPV4_RE.fullmatch(hostname) is not None


def _is_ambiguous_ipv4_text(address: str) -> bool:
    if not _ODD_IPV4_RE.fullmatch(address):
        return False
    parts = address.split(".")
    if len(parts) != 4:
        return True
    for part in parts:
        if not part.isdigit():
            return True
        if len(part) > 1 and part.startswith("0"):
            return True
        number = int(part)
        if number < 0 or number > 255:
            return True
    return False


def _path_traverses(path: str) -> bool:
    decoded = unquote(path)
    parts = decoded.split("/")
    return ".." in parts


def _normalize_path(path: str) -> str:
    normalized = posixpath.normpath(path)
    if not normalized.startswith("/"):
        normalized = f"/{normalized}"
    if path.endswith("/") and not normalized.endswith("/"):
        normalized = f"{normalized}/"
    return _normalize_unreserved_percent(normalized)


def _normalize_unreserved_percent(value: str) -> str:
    def replace(match: re.Match[str]) -> str:
        token = match.group(0)
        char = bytes.fromhex(token[1:]).decode("latin-1")
        if re.fullmatch(r"[A-Za-z0-9._~-]", char):
            return char
        return token.upper()

    return re.sub(r"%[0-9A-Fa-f]{2}", replace, value)


__all__ = [
    "CanonicalResearchUrl",
    "DomainAllowlistPolicy",
    "InMemoryResearchDestinationResolver",
    "ResearchDestinationResolver",
    "ResolvedResearchDestination",
    "canonicalize_research_url",
    "decode_research_text",
    "detect_untrusted_content_instruction_markers",
    "host_is_allowlisted",
    "parse_and_validate_content_type",
    "project_safe_request_headers",
    "project_safe_response_headers",
    "redirect_method_after",
    "validate_character_encoding",
    "validate_domain_allowlist",
    "validate_peer_matches_destination",
    "validate_public_destination_address",
    "validate_redirect_chain",
]
