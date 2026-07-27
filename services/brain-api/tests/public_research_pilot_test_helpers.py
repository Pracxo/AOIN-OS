from __future__ import annotations

import json
from collections.abc import Mapping
from datetime import UTC, datetime, timedelta
from typing import Any

from aion_brain.contracts.knowledge_public_research_pilot import (
    PublicResearchPilotMode,
    PublicResearchPilotResult,
    build_public_research_authorization_envelope,
    build_public_research_claim_specification,
    build_public_research_plan,
    build_public_research_source_candidate,
    public_research_fingerprint,
)
from aion_brain.knowledge_intelligence.public_research_dns import (
    InMemoryPublicResearchDnsBackend,
)
from aion_brain.knowledge_intelligence.public_research_http_transport import (
    InMemoryHttpsFixture,
    InMemoryPinnedHttpsBackend,
)
from aion_brain.knowledge_intelligence.public_research_pilot import (
    ControlledPublicResearchPilot,
)

FIXED_TIME = datetime(2026, 1, 1, tzinfo=UTC)
PUBLIC_IPV4 = "93.184.216.34"
PUBLIC_IPV6 = "2606:4700:4700::1111"


def make_source(
    *,
    url: str = "https://example.com/",
    method: str = "GET",
    source_id: str = "source-0001",
):
    return build_public_research_source_candidate(
        source_candidate_id=source_id,
        query_ids=("query-0001",),
        original_url=url,
        source_class="official_standard",
        source_control_group_id="group-0001",
        expected_content_types=("text/html", "text/plain"),
        method=method,  # type: ignore[arg-type]
    )


def make_claim(binding: str = "public-research-source-snapshot-0001"):
    return build_public_research_claim_specification(
        claim_specification_id="claim-spec-0001",
        claim_id="claim-0001",
        operator_supplied_claim_text="Example low-risk technical standards claim.",
        claim_kind="technical_standard",
        evidence_bindings=(binding,),
        evidence_direction_by_source={binding: "supports"},
        target_valid_time=FIXED_TIME,
        jurisdiction="global",
        version_scope="current",
        domain_codes=("internet",),
    )


def make_plan(
    *,
    mode: PublicResearchPilotMode = PublicResearchPilotMode.DETERMINISTIC_SIMULATION,
    source=None,
    claim=None,
    allowlist: tuple[str, ...] = ("example.com",),
):
    source = source or make_source()
    claim = claim or make_claim()
    return build_public_research_plan(
        pilot_plan_id="plan-0001",
        mode=mode,
        research_plan="Evaluate explicit source evidence through fake backends.",
        explicit_source_candidates=(source,),
        explicit_claim_specifications=(claim,),
        explicit_domain_allowlist=allowlist,
        allowed_content_types=("text/html", "text/plain"),
        created_at=FIXED_TIME,
        expires_at=FIXED_TIME + timedelta(minutes=15),
    )


def make_envelope(
    *, mode: PublicResearchPilotMode = PublicResearchPilotMode.DETERMINISTIC_SIMULATION
):
    return build_public_research_authorization_envelope(
        pilot_session_id="session-0001",
        plan_ids=("plan-0001",),
        operator_identity_fingerprint=public_research_fingerprint({"operator": "test"}),
        live_network_access_approved=mode is PublicResearchPilotMode.OPERATOR_INVOKED_LIVE,
        created_at=FIXED_TIME,
        expires_at=FIXED_TIME + timedelta(minutes=15),
    )


def make_fixture(
    *,
    url: str,
    method: str = "GET",
    status_code: int = 200,
    headers: tuple[tuple[str, str], ...] = (("Content-Type", "text/plain; charset=utf-8"),),
    body: bytes = b"AION public research pilot fixture evidence.",
    peer_address: str = PUBLIC_IPV4,
    certificate_valid: bool = True,
    hostname_valid: bool = True,
    timeout: bool = False,
) -> InMemoryHttpsFixture:
    return InMemoryHttpsFixture(
        method=method,  # type: ignore[arg-type]
        url=url,
        status_code=status_code,
        headers=headers,
        body=body,
        peer_address=peer_address,
        certificate_valid=certificate_valid,
        hostname_valid=hostname_valid,
        timeout=timeout,
    )


def run_simulation(
    *,
    plan=None,
    host_addresses: Mapping[str, tuple[str, ...]] | None = None,
    fixtures: Mapping[tuple[str, str], InMemoryHttpsFixture] | None = None,
    source_body: bytes = b"AION public research pilot fixture evidence.",
    source_headers: tuple[tuple[str, str], ...] = (("Content-Type", "text/plain; charset=utf-8"),),
    source_status: int = 200,
    robots_status: int = 200,
    robots_body: bytes = b"User-agent: *\nAllow: /\n",
    peer_address: str = PUBLIC_IPV4,
) -> PublicResearchPilotResult:
    plan = plan or make_plan()
    source = plan.explicit_source_candidates[0]
    source_url = source.original_url
    robots_url = f"https://{source.domain}/robots.txt"
    resolved_hosts = dict(host_addresses or {source.domain: (PUBLIC_IPV4,)})
    fixture_map = dict(
        fixtures
        or {
            ("GET", robots_url): make_fixture(
                url=robots_url,
                status_code=robots_status,
                body=robots_body,
                peer_address=peer_address,
            ),
            (source.method, source_url): make_fixture(
                url=source_url,
                method=source.method,
                status_code=source_status,
                headers=source_headers,
                body=source_body,
                peer_address=peer_address,
            ),
        }
    )
    dns = InMemoryPublicResearchDnsBackend(resolved_hosts, resolved_at=FIXED_TIME)
    http = InMemoryPinnedHttpsBackend(fixture_map, completed_at=FIXED_TIME)
    pilot = ControlledPublicResearchPilot(
        dns_backend=dns, connection_backend=http, clock=lambda: FIXED_TIME
    )
    return pilot.run(envelope=make_envelope(mode=plan.mode), plans=(plan,))


def body_keys_absent(value: Any) -> bool:
    if isinstance(value, dict):
        for key, item in value.items():
            if key in {"body", "source_body", "content_bytes", "raw_body"}:
                return False
            if not body_keys_absent(item):
                return False
        return True
    if isinstance(value, list):
        return all(body_keys_absent(item) for item in value)
    return True


def result_json(result: PublicResearchPilotResult) -> str:
    return json.dumps(result.model_dump(mode="json"), sort_keys=True)


def committed_live_evidence_path() -> str:
    return "examples/knowledge-intelligence/public-research-pilot-live-evidence-redacted.json"
