"""Controlled public DNS resolution and pinning for AION-219."""

from __future__ import annotations

import ipaddress
import re
import socket as net
from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from typing import Literal, Protocol

from aion_brain.contracts.knowledge_public_research_pilot import (
    PublicResearchDnsResolution,
    PublicResearchDnsStatus,
    PublicResearchPinnedDestination,
    public_research_fingerprint,
    utc_now,
    validate_domain_name,
)

MAXIMUM_ADDRESSES_PER_RESOLUTION = 16
_METADATA_ADDRESSES = {
    ipaddress.ip_address("169.254.169.254"),
    ipaddress.ip_address("100.100.100.200"),
}
_DOCUMENTATION_NETWORKS = (
    ipaddress.ip_network("192.0.2.0/24"),
    ipaddress.ip_network("198.51.100.0/24"),
    ipaddress.ip_network("203.0.113.0/24"),
    ipaddress.ip_network("2001:db8::/32"),
)


class PublicResearchDnsError(ValueError):
    """Raised when public DNS validation fails closed."""

    def __init__(self, status: PublicResearchDnsStatus, message: str = "DNS rejected") -> None:
        super().__init__(message)
        self.status = status


class PublicResearchDnsBackend(Protocol):
    """Explicit DNS backend protocol."""

    def resolve(
        self,
        hostname: str,
        port: int,
        *,
        resolution_id: str,
    ) -> PublicResearchPinnedDestination:
        """Resolve and pin one hostname for one request."""


class DisabledPublicResearchDnsBackend:
    """Default fail-closed DNS backend."""

    system_dns_resolution_available = False

    def resolve(
        self,
        hostname: str,
        port: int,
        *,
        resolution_id: str,
    ) -> PublicResearchPinnedDestination:
        _ = hostname, port, resolution_id
        raise PublicResearchDnsError(PublicResearchDnsStatus.RESOLUTION_FAILED, "DNS disabled")


@dataclass(frozen=True)
class InMemoryPublicResearchDnsBackend:
    """Deterministic no-network DNS backend for CI and tests."""

    host_addresses: dict[str, tuple[str, ...]]
    resolved_at: datetime | None = None

    system_dns_resolution_available = False

    def resolve(
        self,
        hostname: str,
        port: int,
        *,
        resolution_id: str,
    ) -> PublicResearchPinnedDestination:
        normalized = normalize_hostname(hostname)
        addresses = self.host_addresses.get(normalized)
        if not addresses:
            raise PublicResearchDnsError(
                PublicResearchDnsStatus.RESOLUTION_FAILED,
                "DNS fixture unavailable",
            )
        return build_pinned_destination(
            hostname=normalized,
            port=port,
            raw_addresses=addresses,
            resolution_id=resolution_id,
            resolved_at=self.resolved_at,
        )


class SystemPublicResearchDnsBackend:
    """System DNS backend using the platform resolver only."""

    system_dns_resolution_available = True

    def resolve(
        self,
        hostname: str,
        port: int,
        *,
        resolution_id: str,
    ) -> PublicResearchPinnedDestination:
        normalized = normalize_hostname(hostname)
        try:
            infos = net.getaddrinfo(
                normalized,
                port,
                type=net.SOCK_STREAM,
                proto=net.IPPROTO_TCP,
            )
        except net.gaierror as exc:
            raise PublicResearchDnsError(
                PublicResearchDnsStatus.RESOLUTION_FAILED,
                "DNS resolution failed",
            ) from exc
        addresses: list[str] = []
        for family, _, _, _, sockaddr in infos:
            if family not in {net.AF_INET, net.AF_INET6}:
                continue
            addresses.append(str(sockaddr[0]))
        if not addresses:
            raise PublicResearchDnsError(
                PublicResearchDnsStatus.RESOLUTION_FAILED,
                "DNS resolution returned no A or AAAA records",
            )
        return build_pinned_destination(
            hostname=normalized,
            port=port,
            raw_addresses=tuple(addresses),
            resolution_id=resolution_id,
        )


def normalize_hostname(hostname: str) -> str:
    """Normalize a hostname and reject IP literals and ambiguous encodings."""

    normalized = validate_domain_name(hostname, "public research hostname")
    if _looks_like_ip_literal(hostname):
        raise PublicResearchDnsError(
            PublicResearchDnsStatus.REJECTED_AMBIGUOUS,
            "IP-literal hostnames are rejected",
        )
    return normalized


def build_pinned_destination(
    *,
    hostname: str,
    port: int,
    raw_addresses: tuple[str, ...],
    resolution_id: str,
    resolved_at: datetime | None = None,
) -> PublicResearchPinnedDestination:
    """Validate and pin a complete DNS answer set."""

    normalized = normalize_hostname(hostname)
    if not raw_addresses:
        raise PublicResearchDnsError(PublicResearchDnsStatus.RESOLUTION_FAILED, "empty DNS answer")
    unique_addresses = tuple(sorted(dict.fromkeys(raw_addresses)))
    if len(unique_addresses) > MAXIMUM_ADDRESSES_PER_RESOLUTION:
        raise PublicResearchDnsError(
            PublicResearchDnsStatus.REJECTED_TOO_MANY_ADDRESSES,
            "DNS answer contains too many addresses",
        )
    families: dict[str, Literal["IPv4", "IPv6"]] = {}
    address_fingerprints: dict[str, str] = {}
    rejected_status: PublicResearchDnsStatus | None = None
    for address in unique_addresses:
        try:
            parsed = ipaddress.ip_address(address)
        except ValueError as exc:
            raise PublicResearchDnsError(
                PublicResearchDnsStatus.REJECTED_AMBIGUOUS,
                "malformed DNS address",
            ) from exc
        status = classify_public_address(parsed)
        if status is not PublicResearchDnsStatus.RESOLVED_AND_PINNED:
            rejected_status = status
            break
        canonical = parsed.compressed
        families[canonical] = "IPv4" if parsed.version == 4 else "IPv6"
        address_fingerprints[canonical] = public_research_fingerprint(
            {"address": canonical, "hostname": normalized, "port": port}
        )
    if rejected_status is not None:
        raise PublicResearchDnsError(rejected_status, "DNS answer contains prohibited address")
    family_counts = Counter(families.values())
    resolved_at = resolved_at or utc_now()
    resolution_payload = {
        "resolution_id": resolution_id,
        "hostname": normalized,
        "port": port,
        "status": PublicResearchDnsStatus.RESOLVED_AND_PINNED.value,
        "address_family_counts": dict(sorted(family_counts.items())),
        "address_fingerprints": tuple(sorted(address_fingerprints.values())),
        "resolved_at": resolved_at.isoformat(),
    }
    resolution = PublicResearchDnsResolution(
        resolution_id=resolution_id,
        hostname=normalized,
        port=port,
        status=PublicResearchDnsStatus.RESOLVED_AND_PINNED,
        address_family_counts=dict(sorted(family_counts.items())),
        address_fingerprints=tuple(sorted(address_fingerprints.values())),
        host_fingerprint=public_research_fingerprint({"hostname": normalized}),
        resolved_at=resolved_at,
        validation_result="all_addresses_public_and_pinned",
        resolution_fingerprint=public_research_fingerprint(resolution_payload),
    )
    return PublicResearchPinnedDestination(
        hostname=normalized,
        port=port,
        address_family_by_address=dict(sorted(families.items())),
        address_fingerprints_by_address=dict(sorted(address_fingerprints.items())),
        resolution=resolution,
        pinned_destination_fingerprint=public_research_fingerprint(
            {
                "hostname": normalized,
                "port": port,
                "resolution": resolution.resolution_fingerprint,
                "addresses": tuple(sorted(address_fingerprints.values())),
            }
        ),
    )


def classify_public_address(
    address: ipaddress.IPv4Address | ipaddress.IPv6Address,
) -> PublicResearchDnsStatus:
    """Classify one address for public research eligibility."""

    if isinstance(address, ipaddress.IPv6Address) and address.ipv4_mapped is not None:
        return classify_public_address(address.ipv4_mapped)
    if address in _METADATA_ADDRESSES:
        return PublicResearchDnsStatus.REJECTED_METADATA
    if any(address in network for network in _DOCUMENTATION_NETWORKS):
        return PublicResearchDnsStatus.REJECTED_DOCUMENTATION
    if address.is_unspecified:
        return PublicResearchDnsStatus.REJECTED_UNSPECIFIED
    if address.is_loopback:
        return PublicResearchDnsStatus.REJECTED_LOOPBACK
    if address.is_link_local:
        return PublicResearchDnsStatus.REJECTED_LINK_LOCAL
    if address.is_multicast:
        return PublicResearchDnsStatus.REJECTED_MULTICAST
    if address.is_private:
        return PublicResearchDnsStatus.REJECTED_PRIVATE
    if address.is_reserved:
        return PublicResearchDnsStatus.REJECTED_RESERVED
    return PublicResearchDnsStatus.RESOLVED_AND_PINNED


def peer_matches_pinned_destination(
    peer_address: str,
    destination: PublicResearchPinnedDestination,
) -> bool:
    """Return true when the connected peer is inside the pinned address set."""

    try:
        canonical = ipaddress.ip_address(peer_address).compressed
    except ValueError:
        return False
    return canonical in destination.address_family_by_address


def peer_fingerprint(peer_address: str, destination: PublicResearchPinnedDestination) -> str:
    """Return the redacted peer-address fingerprint after pin verification."""

    try:
        canonical = ipaddress.ip_address(peer_address).compressed
    except ValueError as exc:
        raise PublicResearchDnsError(
            PublicResearchDnsStatus.REJECTED_AMBIGUOUS,
            "peer invalid",
        ) from exc
    if canonical not in destination.address_fingerprints_by_address:
        raise PublicResearchDnsError(PublicResearchDnsStatus.REJECTED_AMBIGUOUS, "peer not pinned")
    return destination.address_fingerprints_by_address[canonical]


def _looks_like_ip_literal(value: str) -> bool:
    text = value.strip("[]")
    try:
        ipaddress.ip_address(text)
    except ValueError:
        return bool(
            re.match(
                r"^(0x[0-9a-fA-F]+|0[0-7]+|\d+)([.](0x[0-9a-fA-F]+|0[0-7]+|\d+))*$",
                text,
            )
        )
    return True


__all__ = [
    "DisabledPublicResearchDnsBackend",
    "InMemoryPublicResearchDnsBackend",
    "MAXIMUM_ADDRESSES_PER_RESOLUTION",
    "PublicResearchDnsBackend",
    "PublicResearchDnsError",
    "SystemPublicResearchDnsBackend",
    "build_pinned_destination",
    "classify_public_address",
    "normalize_hostname",
    "peer_fingerprint",
    "peer_matches_pinned_destination",
]
