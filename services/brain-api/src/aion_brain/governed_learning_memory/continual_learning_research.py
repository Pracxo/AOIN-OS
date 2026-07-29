"""Controlled public-research composition adapter for AION-228."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime
from typing import Literal

from aion_brain.contracts.governed_continual_learning import (
    RESOURCE_LIMITS,
    ContinualLearningError,
    ContinualLearningPilotMode,
    ContinualLearningResearchBinding,
    ContinualLearningResearchPlan,
    ContinualLearningResearchSourceBinding,
    ContinualLearningResearchStatus,
    build_record,
    continual_fingerprint,
    domain_allowlist_fingerprint,
    utc_now,
)
from aion_brain.knowledge_intelligence.public_research_dns import (
    InMemoryPublicResearchDnsBackend,
    PublicResearchDnsBackend,
    SystemPublicResearchDnsBackend,
)
from aion_brain.knowledge_intelligence.public_research_http_transport import (
    InMemoryHttpsFixture,
    InMemoryPinnedHttpsBackend,
    PublicResearchConnectionBackend,
    PublicResearchTransportError,
    SystemPinnedHttpsBackend,
)
from aion_brain.knowledge_intelligence.public_research_policy import (
    canonicalize_public_research_url,
    detect_prompt_injection_markers,
    evaluate_robots_policy,
    robots_url_for_source,
)
from aion_brain.knowledge_intelligence.public_research_session import (
    PublicResearchPilotKillSwitch,
)


def _hostname(canonical_url: str) -> str:
    if not canonical_url.startswith("https://"):
        raise ContinualLearningError("only explicit HTTPS sources are allowed")
    authority = canonical_url[len("https://") :].split("/", 1)[0]
    return authority.rsplit("@", 1)[-1].split(":", 1)[0].lower()


def _url_fp(url: str) -> str:
    return continual_fingerprint({"url": canonicalize_public_research_url(url)})


class ControlledContinualLearningResearchAdapter:
    """Adapter over existing controlled DNS, pinned HTTPS, and policy components."""

    def __init__(
        self,
        *,
        mode: ContinualLearningPilotMode,
        dns_backend: PublicResearchDnsBackend | None = None,
        https_backend: PublicResearchConnectionBackend | None = None,
        completed_at: datetime | None = None,
    ) -> None:
        self.mode = mode
        self.completed_at = completed_at or utc_now()
        if mode is ContinualLearningPilotMode.OPERATOR_INVOKED_LIVE:
            self.dns_backend = dns_backend or SystemPublicResearchDnsBackend()
            self.https_backend = https_backend or SystemPinnedHttpsBackend()
        else:
            self.dns_backend = dns_backend or InMemoryPublicResearchDnsBackend(
                {
                    "example.org": ("93.184.216.34",),
                    "iana.org": ("192.0.43.8",),
                    "w3.org": ("128.30.52.100",),
                },
                resolved_at=self.completed_at,
            )
            fixtures: dict[tuple[Literal["GET", "HEAD"], str], InMemoryHttpsFixture] = {}
            fixture_addresses = {
                "example.org": "93.184.216.34",
                "iana.org": "192.0.43.8",
                "w3.org": "128.30.52.100",
            }
            for url in (
                "https://example.org/research.txt",
                "https://iana.org/research.txt",
                "https://w3.org/research.txt",
            ):
                canonical = canonicalize_public_research_url(url)
                robots = robots_url_for_source(canonical)
                peer_address = fixture_addresses[_hostname(canonical)]
                fixtures[("GET", canonical)] = InMemoryHttpsFixture(
                    method="GET",
                    url=canonical,
                    body=b"JSON is a text data-interchange format used for structured data.",
                    peer_address=peer_address,
                )
                fixtures[("GET", robots)] = InMemoryHttpsFixture(
                    method="GET",
                    url=robots,
                    body=b"User-agent: AION-Public-Research-Pilot\nAllow: /\n",
                    peer_address=peer_address,
                )
            self.https_backend = https_backend or InMemoryPinnedHttpsBackend(
                fixtures,
                completed_at=self.completed_at,
            )

    def plan_research(
        self,
        *,
        session_id: str,
        cycle_id: str,
        claim_fingerprint: str,
        explicit_source_urls: tuple[str, ...],
        exact_domains: tuple[str, ...],
        source_control_groups: tuple[str, ...],
    ) -> ContinualLearningResearchPlan:
        """Create a redacted explicit-source research plan."""

        canonical_urls = tuple(
            canonicalize_public_research_url(url) for url in explicit_source_urls
        )
        domains = tuple(sorted({_hostname(url) for url in canonical_urls}))
        if tuple(sorted(exact_domains)) != domains:
            raise ContinualLearningError("exact domain allowlist must match explicit sources")
        if len(canonical_urls) < 3 or len(set(source_control_groups)) < 3:
            raise ContinualLearningError("three independent explicit sources are required")
        return build_record(
            ContinualLearningResearchPlan,
            {
                "plan_id": f"{cycle_id}-research-plan",
                "session_id": session_id,
                "cycle_id": cycle_id,
                "claim_fingerprint": claim_fingerprint,
                "explicit_source_url_fingerprints": tuple(_url_fp(url) for url in canonical_urls),
                "exact_domains": domains,
                "source_control_groups": source_control_groups,
                "created_at": utc_now(),
            },
            "research_plan_fingerprint",
        )

    def acquire_research(
        self,
        *,
        plan: ContinualLearningResearchPlan,
        explicit_source_urls: tuple[str, ...],
        source_control_groups: tuple[str, ...],
    ) -> ContinualLearningResearchBinding:
        """Acquire explicit sources and return redacted, source-body-purged bindings."""

        canonical_urls = tuple(
            canonicalize_public_research_url(url) for url in explicit_source_urls
        )
        if tuple(_url_fp(url) for url in canonical_urls) != plan.explicit_source_url_fingerprints:
            raise ContinualLearningError("research acquisition URL fingerprint mismatch")
        kill_switch = PublicResearchPilotKillSwitch()
        source_bindings: list[ContinualLearningResearchSourceBinding] = []
        total_transfer = 0
        https_count = 0
        for index, (url, group) in enumerate(
            zip(canonical_urls, source_control_groups, strict=True),
            1,
        ):
            host = _hostname(url)
            destination = self.dns_backend.resolve(
                host,
                443,
                resolution_id=f"{plan.cycle_id}-dns-{index}",
            )
            robots_response = self.https_backend.fetch(
                method="GET",
                url=robots_url_for_source(url),
                destination=destination,
                request_id=f"{plan.cycle_id}-robots-request-{index}",
                exchange_id=f"{plan.cycle_id}-robots-exchange-{index}",
                maximum_response_bytes=65_536,
                maximum_total_transfer_bytes=RESOURCE_LIMITS["maximum_transfer_bytes_per_cycle"],
                current_total_transfer_bytes=total_transfer,
                timeout_seconds=RESOURCE_LIMITS["maximum_timeout_seconds_per_request"],
                allowed_content_types=("text/plain",),
                started_at=self._request_started_at(),
                kill_switch=kill_switch,
            )
            https_count += 1
            total_transfer += len(robots_response.body)
            robots_decision = evaluate_robots_policy(
                robots_url=robots_response.final_url,
                target_url=url,
                status_code=robots_response.status_code,
                headers=robots_response.raw_headers,
                body=robots_response.body,
            )
            robots_response.purge_body()
            if not robots_decision.allowed:
                raise ContinualLearningError("robots policy rejected explicit source")
            response = self.https_backend.fetch(
                method="GET",
                url=url,
                destination=destination,
                request_id=f"{plan.cycle_id}-source-request-{index}",
                exchange_id=f"{plan.cycle_id}-source-exchange-{index}",
                maximum_response_bytes=RESOURCE_LIMITS["maximum_response_bytes_per_source"],
                maximum_total_transfer_bytes=RESOURCE_LIMITS["maximum_transfer_bytes_per_cycle"],
                current_total_transfer_bytes=total_transfer,
                timeout_seconds=RESOURCE_LIMITS["maximum_timeout_seconds_per_request"],
                allowed_content_types=(
                    "text/html",
                    "text/plain",
                    "application/json",
                    "application/xml",
                ),
                started_at=self._request_started_at(),
                kill_switch=kill_switch,
            )
            https_count += 1
            total_transfer += len(response.body)
            if detect_prompt_injection_markers(response.body):
                response.purge_body()
                raise ContinualLearningError("source contains instruction-like untrusted content")
            provenance_fingerprint = continual_fingerprint(
                {
                    "source": response.exchange_metadata.exchange_fingerprint,
                    "domain": domain_allowlist_fingerprint((host,)),
                    "group": group,
                    "body_purged": True,
                }
            )
            citation_fingerprint = continual_fingerprint(
                {"citation": response.exchange_metadata.exchange_fingerprint}
            )
            response.purge_body()
            source_bindings.append(
                build_record(
                    ContinualLearningResearchSourceBinding,
                    {
                        "source_binding_id": f"{plan.cycle_id}-source-{index}",
                        "cycle_id": plan.cycle_id,
                        "url_fingerprint": _url_fp(url),
                        "domain_fingerprint": domain_allowlist_fingerprint((host,)),
                        "source_control_group": group,
                        "dns_resolution_fingerprint": destination.resolution.resolution_fingerprint,
                        "http_exchange_fingerprint": (
                            response.exchange_metadata.exchange_fingerprint
                        ),
                        "robots_policy_fingerprint": robots_decision.fingerprint,
                        "provenance_fingerprint": provenance_fingerprint,
                        "citation_fingerprint": citation_fingerprint,
                        "created_at": utc_now(),
                    },
                    "source_binding_fingerprint",
                )
            )
        return build_record(
            ContinualLearningResearchBinding,
            {
                "schema_version": "aion-glm-continual-learning-research-binding/v1",
                "binding_id": f"{plan.cycle_id}-research-binding",
                "session_id": plan.session_id,
                "cycle_id": plan.cycle_id,
                "status": ContinualLearningResearchStatus.ACQUIRED,
                "source_bindings": tuple(source_bindings),
                "claim_fingerprint": plan.claim_fingerprint,
                "source_fetch_count": len(source_bindings),
                "dns_resolution_count": len(source_bindings),
                "public_https_request_count": https_count,
                "source_body_purge_count": len(source_bindings),
                "created_at": utc_now(),
            },
            "research_binding_fingerprint",
        )

    def _request_started_at(self) -> datetime:
        if self.mode is ContinualLearningPilotMode.DETERMINISTIC_SIMULATION:
            return self.completed_at
        return utc_now()


def deterministic_research_adapter(
    *,
    fixtures: Mapping[tuple[Literal["GET", "HEAD"], str], InMemoryHttpsFixture] | None = None,
    dns_hosts: Mapping[str, tuple[str, ...]] | None = None,
) -> ControlledContinualLearningResearchAdapter:
    """Return a deterministic adapter for CI with no public network access."""

    now = utc_now()
    dns_backend = InMemoryPublicResearchDnsBackend(
        dict(dns_hosts or {"example.org": ("93.184.216.34",)}),
        resolved_at=now,
    )
    https_backend = None
    if fixtures is not None:
        https_backend = InMemoryPinnedHttpsBackend(fixtures, completed_at=now)
    return ControlledContinualLearningResearchAdapter(
        mode=ContinualLearningPilotMode.DETERMINISTIC_SIMULATION,
        dns_backend=dns_backend,
        https_backend=https_backend,
        completed_at=now,
    )


def classify_research_error(error: Exception) -> str:
    """Return a redacted reason code for a research acquisition failure."""

    if isinstance(error, PublicResearchTransportError):
        return error.reason_code
    return "continual_learning_research_failed_closed"
