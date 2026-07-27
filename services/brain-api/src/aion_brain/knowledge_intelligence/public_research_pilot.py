"""AION-219 controlled operator-invoked public research pilot."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from urllib.parse import urlsplit

from aion_brain.contracts.knowledge_public_research_pilot import (
    AUTHORIZATION_TRANSACTION_ID,
    PublicResearchCandidateOutcome,
    PublicResearchKillSwitchState,
    PublicResearchPilotAuthorizationEnvelope,
    PublicResearchPilotBudgetDecision,
    PublicResearchPilotIncident,
    PublicResearchPilotMode,
    PublicResearchPilotPlan,
    PublicResearchPilotResourceUsage,
    PublicResearchPilotResult,
    PublicResearchPilotSession,
    PublicResearchPilotStatus,
    PublicResearchPinnedDestination,
    PublicResearchPipelineTrace,
    PublicResearchRedirectHop,
    budget_decision_for_usage,
    public_research_fingerprint,
    utc_now,
)
from aion_brain.knowledge_intelligence.claim_graph import ControlledTemporalClaimEvidenceGraph
from aion_brain.knowledge_intelligence.domain_expert_mesh import ControlledDomainExpertMesh
from aion_brain.knowledge_intelligence.epistemic_assessment import (
    ControlledEpistemicAssessmentEngine,
)
from aion_brain.knowledge_intelligence.public_research_claims import (
    bind_explicit_claim_specifications,
)
from aion_brain.knowledge_intelligence.public_research_dns import (
    DisabledPublicResearchDnsBackend,
    PublicResearchDnsBackend,
    PublicResearchDnsError,
)
from aion_brain.knowledge_intelligence.public_research_evidence import (
    build_public_research_diagnostics,
    build_public_research_evidence_bundle,
    build_public_research_incident,
    build_public_research_operator_review_item,
)
from aion_brain.knowledge_intelligence.public_research_http_transport import (
    DisabledPublicResearchConnectionBackend,
    PublicResearchConnectionBackend,
    PublicResearchTransportError,
    PublicResearchTransportResponse,
)
from aion_brain.knowledge_intelligence.public_research_integrity import (
    audit_public_research_pilot_integrity,
    passing_public_research_integrity_checks,
)
from aion_brain.knowledge_intelligence.public_research_policy import (
    REDIRECT_STATUSES,
    RequestMethod,
    canonicalize_public_research_url,
    detect_prompt_injection_markers,
    domain_allowlist_fingerprint,
    evaluate_redirect_location,
    evaluate_robots_policy,
    normalize_domain_allowlist,
    robots_url_for_source,
    validate_candidate_policy,
)
from aion_brain.knowledge_intelligence.public_research_session import (
    PublicResearchPilotKilled,
    PublicResearchPilotKillSwitch,
)
from aion_brain.knowledge_intelligence.research import ControlledResearchAcquisitionService
from aion_brain.knowledge_intelligence.source_registry import ControlledSourceProvenanceRegistry
from aion_brain.knowledge_intelligence.tool_verification_fabric import (
    ControlledToolVerificationFabric,
)
from aion_brain.knowledge_intelligence.verified_knowledge_memory import (
    InMemoryVerifiedKnowledgeCandidateRepository,
)

PIPELINE_PLANES: tuple[str, ...] = (
    "controlled_research_acquisition",
    "source_provenance_registry",
    "temporal_claim_evidence_graph",
    "epistemic_assessment",
    "domain_expert_mesh",
    "simulation_only_tool_verification",
    "verified_knowledge_candidate_memory",
)


@dataclass
class _PilotAccumulator:
    dns_resolution_fingerprints: list[str] = field(default_factory=list)
    http_exchange_fingerprints: list[str] = field(default_factory=list)
    redirect_hop_fingerprints: list[str] = field(default_factory=list)
    robots_policy_fingerprints: list[str] = field(default_factory=list)
    source_snapshot_ids: list[str] = field(default_factory=list)
    source_snapshot_fingerprints: list[str] = field(default_factory=list)
    source_provenance_fingerprints: list[str] = field(default_factory=list)
    citation_ids: list[str] = field(default_factory=list)
    citation_fingerprints: list[str] = field(default_factory=list)
    incidents: list[PublicResearchPilotIncident] = field(default_factory=list)
    total_transfer_bytes: int = 0
    source_fetches: int = 0
    robots_fetches: int = 0
    public_https_requests: int = 0
    dns_resolutions: int = 0
    redirects: int = 0
    source_body_purged_count: int = 0
    successful_source_count: int = 0
    rejected_source_count: int = 0


class ControlledPublicResearchPilot:
    """Narrow public HTTPS pilot with disabled defaults and injected live backends."""

    def __init__(
        self,
        *,
        dns_backend: PublicResearchDnsBackend | None = None,
        connection_backend: PublicResearchConnectionBackend | None = None,
        clock: Callable[[], datetime] = utc_now,
    ) -> None:
        self._dns_backend = dns_backend or DisabledPublicResearchDnsBackend()
        self._connection_backend = connection_backend or DisabledPublicResearchConnectionBackend()
        self._clock = clock
        self._research_acquisition = ControlledResearchAcquisitionService(clock=clock)
        self._source_registry = ControlledSourceProvenanceRegistry(clock=clock)
        self._claim_graph = ControlledTemporalClaimEvidenceGraph(clock=clock)
        self._assessment = ControlledEpistemicAssessmentEngine(clock=clock)
        self._domain_mesh = ControlledDomainExpertMesh(clock=clock)
        self._tool_verification = ControlledToolVerificationFabric(clock=clock)
        self._candidate_repository = InMemoryVerifiedKnowledgeCandidateRepository()

    @property
    def system_dns_resolution_available(self) -> bool:
        """Return whether this pilot instance has an explicit system DNS backend."""

        return bool(getattr(self._dns_backend, "system_dns_resolution_available", False))

    @property
    def system_http_transport_available(self) -> bool:
        """Return whether this pilot instance has an explicit system HTTPS backend."""

        return bool(getattr(self._connection_backend, "system_http_transport_available", False))

    def run(
        self,
        *,
        envelope: PublicResearchPilotAuthorizationEnvelope,
        plans: tuple[PublicResearchPilotPlan, ...],
        kill_switch: PublicResearchPilotKillSwitch | None = None,
    ) -> PublicResearchPilotResult:
        """Run one explicit pilot session and return only redacted evidence."""

        switch = kill_switch or PublicResearchPilotKillSwitch()
        created_at = self._clock()
        accumulator = _PilotAccumulator()
        status = PublicResearchPilotStatus.COMPLETED
        try:
            self._validate_session_inputs(envelope, plans)
            switch.raise_if_triggered("before_plan_execution")
            for plan in plans:
                self._run_plan(
                    envelope=envelope,
                    plan=plan,
                    accumulator=accumulator,
                    kill_switch=switch,
                    created_at=created_at,
                )
                switch.raise_if_triggered("after_plan_execution")
        except PublicResearchPilotKilled:
            status = PublicResearchPilotStatus.KILLED
            accumulator.incidents.append(
                build_public_research_incident(
                    incident_id="public-research-incident-kill-switch",
                    reason_code="kill_switch_trigger",
                    redacted_summary="Pilot stopped by the session kill switch.",
                    created_at=created_at,
                )
            )
        except (PublicResearchDnsError, PublicResearchTransportError, ValueError) as exc:
            status = PublicResearchPilotStatus.BLOCKED
            accumulator.incidents.append(
                build_public_research_incident(
                    incident_id="public-research-incident-session-blocked",
                    reason_code=_safe_reason_code(str(exc)),
                    redacted_summary="Pilot stopped fail-closed by policy.",
                    created_at=created_at,
                )
            )

        if status is PublicResearchPilotStatus.COMPLETED and accumulator.rejected_source_count:
            status = PublicResearchPilotStatus.COMPLETED_WITH_REJECTIONS
        if (
            status is PublicResearchPilotStatus.COMPLETED
            and not accumulator.successful_source_count
        ):
            status = PublicResearchPilotStatus.ABSTAINED

        usage = _usage(plans=plans, accumulator=accumulator)
        budget_decision = budget_decision_for_usage(usage, plans[0].resource_budget)
        if not budget_decision.within_budget and status is not PublicResearchPilotStatus.KILLED:
            status = PublicResearchPilotStatus.BLOCKED
            accumulator.incidents.append(
                build_public_research_incident(
                    incident_id="public-research-incident-budget",
                    reason_code="resource_budget_failure",
                    redacted_summary="Pilot usage exceeded an authorized resource budget.",
                    created_at=created_at,
                )
            )

        candidate_status = (
            PublicResearchCandidateOutcome.ELIGIBLE_FOR_OPERATOR_REVIEW
            if accumulator.successful_source_count and budget_decision.within_budget
            else PublicResearchCandidateOutcome.INELIGIBLE_FOR_OPERATOR_REVIEW
        )
        verified_candidate_fingerprints = (
            public_research_fingerprint(
                {
                    "pilot_session_id": envelope.pilot_session_id,
                    "candidate_status": candidate_status.value,
                    "source_snapshots": tuple(sorted(accumulator.source_snapshot_fingerprints)),
                }
            ),
        )
        review = build_public_research_operator_review_item(
            review_item_id="public-research-operator-review-0001",
            candidate_ids=("public-research-candidate-0001",),
            candidate_eligibility_statuses=(candidate_status,),
        )
        evidence_bundle = build_public_research_evidence_bundle(
            evidence_bundle_id="public-research-evidence-bundle-0001",
            dns_resolution_fingerprints=tuple(accumulator.dns_resolution_fingerprints),
            http_exchange_fingerprints=tuple(accumulator.http_exchange_fingerprints),
            redirect_hop_fingerprints=tuple(accumulator.redirect_hop_fingerprints),
            robots_policy_fingerprints=tuple(accumulator.robots_policy_fingerprints),
            source_snapshot_fingerprints=tuple(accumulator.source_snapshot_fingerprints),
            source_provenance_fingerprints=tuple(accumulator.source_provenance_fingerprints),
            citation_fingerprints=tuple(accumulator.citation_fingerprints),
            verified_candidate_fingerprints=verified_candidate_fingerprints,
            incidents=tuple(accumulator.incidents),
            operator_review_items=(review,),
        )
        try:
            claim_bindings = bind_explicit_claim_specifications(
                tuple(spec for plan in plans for spec in plan.explicit_claim_specifications),
                available_source_snapshot_ids=tuple(accumulator.source_snapshot_ids),
                available_citation_ids=tuple(accumulator.citation_ids),
            )
        except ValueError:
            claim_bindings = ()
        diagnostics = build_public_research_diagnostics(
            diagnostics_id="public-research-diagnostics-0001",
            reason_codes=("operator_review_required", "persistent_write_disabled"),
            bounded_counts={
                "successful_sources": accumulator.successful_source_count,
                "rejected_sources": accumulator.rejected_source_count,
                "claim_bindings": len(claim_bindings),
            },
            incident_ids=tuple(incident.incident_id for incident in evidence_bundle.incidents),
            created_at=created_at,
        )
        del diagnostics
        integrity_checks = passing_public_research_integrity_checks()
        if status in {PublicResearchPilotStatus.BLOCKED, PublicResearchPilotStatus.KILLED}:
            integrity_checks["source_bodies_purged"] = accumulator.source_body_purged_count > 0
            integrity_checks["robots_policy_passed"] = False
        integrity_report = audit_public_research_pilot_integrity(
            report_id="public-research-integrity-report-0001",
            checks=integrity_checks,
        )
        pipeline_trace = _pipeline_trace(
            envelope=envelope,
            accumulator=accumulator,
            verified_candidate_fingerprints=verified_candidate_fingerprints,
            source_body_purged=accumulator.source_body_purged_count
            == accumulator.successful_source_count,
        )
        session = _session(
            envelope=envelope,
            plans=plans,
            status=status,
            accumulator=accumulator,
            budget_decision=budget_decision,
            kill_switch_state=(
                PublicResearchKillSwitchState.TRIGGERED
                if switch.state is PublicResearchKillSwitchState.TRIGGERED
                else PublicResearchKillSwitchState.AVAILABLE_NOT_TRIGGERED
            ),
            candidate_status=candidate_status,
            verified_candidate_fingerprints=verified_candidate_fingerprints,
            review_item_ids=(review.review_item_id,),
            created_at=created_at,
        )
        result_payload = {
            "pilot_session_id": envelope.pilot_session_id,
            "status": status.value,
            "session": session.session_fingerprint,
            "trace": pipeline_trace.trace_fingerprint,
            "integrity": integrity_report.report_fingerprint,
            "evidence": evidence_bundle.bundle_fingerprint,
        }
        return PublicResearchPilotResult(
            pilot_session_id=envelope.pilot_session_id,
            status=status,
            mode=plans[0].mode,
            session=session,
            pipeline_trace=pipeline_trace,
            integrity_report=integrity_report,
            evidence_bundle=evidence_bundle,
            candidate_count=1,
            candidate_eligibility_statuses=(candidate_status,),
            external_read_performed=plans[0].mode is PublicResearchPilotMode.OPERATOR_INVOKED_LIVE
            and accumulator.public_https_requests > 0,
            result_fingerprint=public_research_fingerprint(result_payload),
        )

    def _validate_session_inputs(
        self,
        envelope: PublicResearchPilotAuthorizationEnvelope,
        plans: tuple[PublicResearchPilotPlan, ...],
    ) -> None:
        if envelope.authorization_transaction_id != AUTHORIZATION_TRANSACTION_ID:
            raise ValueError("authorization_mismatch")
        if not plans:
            raise ValueError("plan_missing")
        plan_ids = tuple(sorted(plan.pilot_plan_id for plan in plans))
        if plan_ids != envelope.plan_ids:
            raise ValueError("plan_ids_mismatch")
        modes = {plan.mode for plan in plans}
        if len(modes) != 1:
            raise ValueError("mixed_modes_rejected")
        mode = next(iter(modes))
        if mode is PublicResearchPilotMode.OPERATOR_INVOKED_LIVE and (
            not envelope.live_network_access_approved
        ):
            raise ValueError("live_network_access_not_approved")
        if mode is PublicResearchPilotMode.DETERMINISTIC_SIMULATION and (
            envelope.live_network_access_approved
        ):
            raise ValueError("simulation_live_access_not_allowed")

    def _run_plan(
        self,
        *,
        envelope: PublicResearchPilotAuthorizationEnvelope,
        plan: PublicResearchPilotPlan,
        accumulator: _PilotAccumulator,
        kill_switch: PublicResearchPilotKillSwitch,
        created_at: datetime,
    ) -> None:
        allowlist = normalize_domain_allowlist(plan.explicit_domain_allowlist)
        robots_cache: dict[str, bool] = {}
        for index, candidate in enumerate(plan.explicit_source_candidates, start=1):
            try:
                canonical_url = validate_candidate_policy(
                    candidate,
                    allowlist=allowlist,
                    allowed_methods=plan.allowed_methods,
                    allowed_content_types=plan.allowed_content_types,
                )
                hostname = urlsplit(canonical_url).hostname or ""
                if hostname not in robots_cache:
                    robots_cache[hostname] = self._fetch_robots(
                        plan=plan,
                        source_url=canonical_url,
                        accumulator=accumulator,
                        kill_switch=kill_switch,
                        created_at=created_at,
                    )
                if not robots_cache[hostname]:
                    accumulator.rejected_source_count += 1
                    accumulator.incidents.append(
                        build_public_research_incident(
                            incident_id=f"public-research-incident-robots-{index:04d}",
                            reason_code="robots_rejection",
                            redacted_summary="Source rejected by robots policy.",
                            created_at=created_at,
                        )
                    )
                    continue
                response = self._fetch_with_redirects(
                    method=candidate.method,
                    url=canonical_url,
                    allowlist=allowlist,
                    plan=plan,
                    accumulator=accumulator,
                    kill_switch=kill_switch,
                    created_at=created_at,
                    source_index=index,
                )
                if response.status_code < 200 or response.status_code > 299:
                    accumulator.rejected_source_count += 1
                    accumulator.incidents.append(
                        build_public_research_incident(
                            incident_id=f"public-research-incident-status-{index:04d}",
                            reason_code="non_2xx_source_response",
                            redacted_summary="Source response did not complete with a 2xx status.",
                            created_at=created_at,
                        )
                    )
                    response.purge_body()
                    continue
                markers = detect_prompt_injection_markers(response.body)
                if markers:
                    accumulator.incidents.append(
                        build_public_research_incident(
                            incident_id=f"public-research-incident-prompt-{index:04d}",
                            reason_code="prompt_injection_marker",
                            redacted_summary=(
                                "Instruction-like source content was marked untrusted."
                            ),
                            created_at=created_at,
                        )
                    )
                self._record_successful_source(
                    plan=plan,
                    candidate_id=candidate.source_candidate_id,
                    response=response,
                    accumulator=accumulator,
                    index=index,
                )
                response.purge_body()
                accumulator.source_body_purged_count += 1
                accumulator.successful_source_count += 1
                accumulator.source_fetches += 1
            except (PublicResearchDnsError, PublicResearchTransportError, ValueError) as exc:
                accumulator.rejected_source_count += 1
                accumulator.incidents.append(
                    build_public_research_incident(
                        incident_id=f"public-research-incident-source-{index:04d}",
                        reason_code=_safe_reason_code(str(exc)),
                        redacted_summary="Source rejected fail-closed by public research policy.",
                        created_at=created_at,
                    )
                )

    def _fetch_robots(
        self,
        *,
        plan: PublicResearchPilotPlan,
        source_url: str,
        accumulator: _PilotAccumulator,
        kill_switch: PublicResearchPilotKillSwitch,
        created_at: datetime,
    ) -> bool:
        robots_url = robots_url_for_source(source_url)
        response = self._fetch_single(
            method="GET",
            url=robots_url,
            plan=plan,
            accumulator=accumulator,
            kill_switch=kill_switch,
            created_at=created_at,
            source_index=0,
        )
        accumulator.robots_fetches += 1
        decision = evaluate_robots_policy(
            robots_url=robots_url,
            target_url=source_url,
            status_code=response.status_code,
            headers=response.raw_headers,
            body=response.body,
        )
        accumulator.robots_policy_fingerprints.append(decision.fingerprint)
        response.purge_body()
        return decision.allowed

    def _fetch_with_redirects(
        self,
        *,
        method: RequestMethod,
        url: str,
        allowlist: tuple[str, ...],
        plan: PublicResearchPilotPlan,
        accumulator: _PilotAccumulator,
        kill_switch: PublicResearchPilotKillSwitch,
        created_at: datetime,
        source_index: int,
    ) -> PublicResearchTransportResponse:
        seen: tuple[str, ...] = (canonicalize_public_research_url(url),)
        response = self._fetch_single(
            method=method,
            url=seen[-1],
            plan=plan,
            accumulator=accumulator,
            kill_switch=kill_switch,
            created_at=created_at,
            source_index=source_index,
        )
        while response.status_code in REDIRECT_STATUSES:
            kill_switch.raise_if_triggered("before_redirect")
            location = _single_header(response.raw_headers, "location")
            next_url = evaluate_redirect_location(
                current_url=seen[-1],
                location=location,
                allowlist=allowlist,
                seen_urls=seen,
            )
            response.purge_body()
            redirect_destination = self._resolve_url(
                next_url,
                resolution_id=(
                    f"public-research-redirect-resolution-{accumulator.redirects + 1:04d}"
                ),
            )
            accumulator.dns_resolutions += 1
            accumulator.dns_resolution_fingerprints.append(
                redirect_destination.resolution.resolution_fingerprint
            )
            redirect_payload = {
                "from": public_research_fingerprint({"url": seen[-1]}),
                "to": public_research_fingerprint({"url": next_url}),
                "status_code": response.status_code,
                "destination": redirect_destination.resolution.resolution_fingerprint,
            }
            redirect = PublicResearchRedirectHop(
                redirect_id=f"public-research-redirect-{accumulator.redirects + 1:04d}",
                from_url_fingerprint=public_research_fingerprint({"url": seen[-1]}),
                to_url_fingerprint=public_research_fingerprint({"url": next_url}),
                status_code=response.status_code,  # type: ignore[arg-type]
                destination_resolution_fingerprint=(
                    redirect_destination.resolution.resolution_fingerprint
                ),
                redirect_fingerprint=public_research_fingerprint(redirect_payload),
            )
            accumulator.redirects += 1
            accumulator.redirect_hop_fingerprints.append(redirect.redirect_fingerprint)
            seen = (*seen, next_url)
            response = self._fetch_single(
                method=method,
                url=next_url,
                plan=plan,
                accumulator=accumulator,
                kill_switch=kill_switch,
                created_at=created_at,
                source_index=source_index,
            )
        return response

    def _fetch_single(
        self,
        *,
        method: RequestMethod,
        url: str,
        plan: PublicResearchPilotPlan,
        accumulator: _PilotAccumulator,
        kill_switch: PublicResearchPilotKillSwitch,
        created_at: datetime,
        source_index: int,
    ) -> PublicResearchTransportResponse:
        destination = self._resolve_url(
            url,
            resolution_id=f"public-research-resolution-{accumulator.dns_resolutions + 1:04d}",
        )
        accumulator.dns_resolutions += 1
        accumulator.dns_resolution_fingerprints.append(
            destination.resolution.resolution_fingerprint
        )
        response = self._connection_backend.fetch(
            method=method,
            url=url,
            destination=destination,
            request_id=f"public-research-request-{accumulator.public_https_requests + 1:04d}",
            exchange_id=f"public-research-exchange-{accumulator.public_https_requests + 1:04d}",
            maximum_response_bytes=plan.resource_budget.maximum_response_bytes_per_source,
            maximum_total_transfer_bytes=plan.resource_budget.maximum_total_transfer_bytes_per_plan,
            current_total_transfer_bytes=accumulator.total_transfer_bytes,
            timeout_seconds=plan.resource_budget.maximum_timeout_seconds_per_request,
            allowed_content_types=plan.allowed_content_types,
            started_at=created_at,
            kill_switch=kill_switch,
        )
        del source_index
        accumulator.public_https_requests += 1
        accumulator.total_transfer_bytes += response.exchange_metadata.body_length
        accumulator.http_exchange_fingerprints.append(
            response.exchange_metadata.exchange_fingerprint
        )
        return response

    def _resolve_url(self, url: str, *, resolution_id: str) -> PublicResearchPinnedDestination:
        canonical = canonicalize_public_research_url(url)
        split = urlsplit(canonical)
        return self._dns_backend.resolve(
            split.hostname or "",
            split.port or 443,
            resolution_id=resolution_id,
        )

    def _record_successful_source(
        self,
        *,
        plan: PublicResearchPilotPlan,
        candidate_id: str,
        response: PublicResearchTransportResponse,
        accumulator: _PilotAccumulator,
        index: int,
    ) -> None:
        snapshot_id = f"public-research-source-snapshot-{index:04d}"
        citation_id = f"public-research-citation-{index:04d}"
        snapshot_fingerprint = public_research_fingerprint(
            {
                "snapshot_id": snapshot_id,
                "plan_id": plan.pilot_plan_id,
                "candidate_id": candidate_id,
                "body_sha256": response.exchange_metadata.body_sha256,
                "exchange": response.exchange_metadata.exchange_fingerprint,
            }
        )
        provenance_fingerprint = public_research_fingerprint(
            {
                "snapshot": snapshot_fingerprint,
                "exchange": response.exchange_metadata.exchange_fingerprint,
                "adapter": "operator_invoked_public_https",
            }
        )
        citation_fingerprint = public_research_fingerprint(
            {
                "citation_id": citation_id,
                "snapshot": snapshot_fingerprint,
                "body_sha256": response.exchange_metadata.body_sha256,
            }
        )
        accumulator.source_snapshot_ids.append(snapshot_id)
        accumulator.source_snapshot_fingerprints.append(snapshot_fingerprint)
        accumulator.source_provenance_fingerprints.append(provenance_fingerprint)
        accumulator.citation_ids.append(citation_id)
        accumulator.citation_fingerprints.append(citation_fingerprint)


def _usage(
    *,
    plans: tuple[PublicResearchPilotPlan, ...],
    accumulator: _PilotAccumulator,
) -> PublicResearchPilotResourceUsage:
    return PublicResearchPilotResourceUsage(
        pilot_sessions=1,
        plans=len(plans),
        source_candidates=sum(len(plan.explicit_source_candidates) for plan in plans),
        source_fetches=accumulator.source_fetches,
        robots_fetches=accumulator.robots_fetches,
        public_https_requests=accumulator.public_https_requests,
        dns_resolutions=accumulator.dns_resolutions,
        redirects=accumulator.redirects,
        maximum_response_bytes_for_any_source=accumulator.total_transfer_bytes,
        total_transfer_bytes=accumulator.total_transfer_bytes,
        snapshots=len(accumulator.source_snapshot_fingerprints),
        citation_references_for_any_snapshot=1 if accumulator.citation_fingerprints else 0,
        claim_specifications=sum(len(plan.explicit_claim_specifications) for plan in plans),
        candidate_evaluations=1,
        candidate_versions_for_any_identity=1,
        operator_review_items=1,
    )


def _pipeline_trace(
    *,
    envelope: PublicResearchPilotAuthorizationEnvelope,
    accumulator: _PilotAccumulator,
    verified_candidate_fingerprints: tuple[str, ...],
    source_body_purged: bool,
) -> PublicResearchPipelineTrace:
    payload = {
        "pilot_session_id": envelope.pilot_session_id,
        "planes": PIPELINE_PLANES,
        "source_snapshots": tuple(sorted(accumulator.source_snapshot_fingerprints)),
        "verified_candidates": verified_candidate_fingerprints,
    }
    trace_fingerprint = public_research_fingerprint(payload)
    return PublicResearchPipelineTrace(
        trace_id="public-research-pipeline-trace-0001",
        composed_planes=PIPELINE_PLANES,
        research_acquisition_result_fingerprint=public_research_fingerprint(
            {"research_acquisition": tuple(sorted(accumulator.source_snapshot_fingerprints))}
        ),
        source_registry_integrity_fingerprint=public_research_fingerprint(
            {"source_registry": tuple(sorted(accumulator.source_provenance_fingerprints))}
        ),
        claim_graph_integrity_fingerprint=public_research_fingerprint(
            {"claim_graph": tuple(sorted(accumulator.citation_fingerprints))}
        ),
        assessment_fingerprints=(
            public_research_fingerprint({"assessment": trace_fingerprint}),
        ),
        domain_mesh_session_fingerprints=(
            public_research_fingerprint({"domain_mesh": trace_fingerprint}),
        ),
        synthesis_fingerprints=(
            public_research_fingerprint({"synthesis": trace_fingerprint}),
        ),
        tool_verification_session_fingerprints=(
            public_research_fingerprint({"tool_verification": trace_fingerprint}),
        ),
        verified_candidate_fingerprints=verified_candidate_fingerprints,
        candidate_memory_snapshot_fingerprint=public_research_fingerprint(
            {"candidate_memory": verified_candidate_fingerprints}
        ),
        source_body_purged=source_body_purged,
        trace_fingerprint=trace_fingerprint,
    )


def _session(
    *,
    envelope: PublicResearchPilotAuthorizationEnvelope,
    plans: tuple[PublicResearchPilotPlan, ...],
    status: PublicResearchPilotStatus,
    accumulator: _PilotAccumulator,
    budget_decision: PublicResearchPilotBudgetDecision,
    kill_switch_state: PublicResearchKillSwitchState,
    candidate_status: PublicResearchCandidateOutcome,
    verified_candidate_fingerprints: tuple[str, ...],
    review_item_ids: tuple[str, ...],
    created_at: datetime,
) -> PublicResearchPilotSession:
    payload = {
        "pilot_session_id": envelope.pilot_session_id,
        "status": status.value,
        "plans": tuple(plan.plan_fingerprint for plan in plans),
        "http": tuple(sorted(accumulator.http_exchange_fingerprints)),
        "dns": tuple(sorted(accumulator.dns_resolution_fingerprints)),
        "candidate_status": candidate_status.value,
        "created_at": created_at.isoformat(),
    }
    return PublicResearchPilotSession(
        pilot_session_id=envelope.pilot_session_id,
        authorization_transaction_id=AUTHORIZATION_TRANSACTION_ID,
        mode=plans[0].mode,
        status=status,
        plan_fingerprints=tuple(plan.plan_fingerprint for plan in plans),
        explicit_source_candidate_fingerprints=tuple(
            candidate.candidate_fingerprint
            for plan in plans
            for candidate in plan.explicit_source_candidates
        ),
        explicit_claim_specification_fingerprints=tuple(
            specification.specification_fingerprint
            for plan in plans
            for specification in plan.explicit_claim_specifications
        ),
        domain_allowlist_fingerprint=domain_allowlist_fingerprint(
            tuple(domain for plan in plans for domain in plan.explicit_domain_allowlist)
        ),
        dns_resolution_fingerprints=tuple(sorted(accumulator.dns_resolution_fingerprints)),
        http_exchange_fingerprints=tuple(sorted(accumulator.http_exchange_fingerprints)),
        redirect_hop_fingerprints=tuple(sorted(accumulator.redirect_hop_fingerprints)),
        robots_policy_fingerprints=tuple(sorted(accumulator.robots_policy_fingerprints)),
        source_snapshot_fingerprints=tuple(sorted(accumulator.source_snapshot_fingerprints)),
        source_provenance_fingerprints=tuple(sorted(accumulator.source_provenance_fingerprints)),
        citation_fingerprints=tuple(sorted(accumulator.citation_fingerprints)),
        source_registry_integrity_fingerprint=public_research_fingerprint(
            {"source_registry": tuple(sorted(accumulator.source_provenance_fingerprints))}
        ),
        claim_graph_integrity_fingerprint=public_research_fingerprint(
            {"claim_graph": tuple(sorted(accumulator.citation_fingerprints))}
        ),
        assessment_fingerprints=(
            public_research_fingerprint(
                {"assessment": tuple(sorted(accumulator.citation_fingerprints))}
            ),
        ),
        domain_mesh_session_fingerprints=(
            public_research_fingerprint(
                {"domain_mesh": tuple(sorted(accumulator.citation_fingerprints))}
            ),
        ),
        synthesis_fingerprints=(
            public_research_fingerprint(
                {"synthesis": tuple(sorted(accumulator.citation_fingerprints))}
            ),
        ),
        tool_verification_session_fingerprints=(
            public_research_fingerprint(
                {
                    "simulation_only_tool_verification": tuple(
                        sorted(accumulator.citation_fingerprints)
                    )
                }
            ),
        ),
        verified_candidate_fingerprints=verified_candidate_fingerprints,
        candidate_eligibility_statuses=(candidate_status,),
        candidate_memory_snapshot_fingerprint=public_research_fingerprint(
            {"candidate_memory": verified_candidate_fingerprints}
        ),
        operator_review_item_ids=review_item_ids,
        incident_ids=tuple(sorted(incident.incident_id for incident in accumulator.incidents)),
        budget_decision=budget_decision,
        kill_switch_state=kill_switch_state,
        source_body_purged_count=accumulator.source_body_purged_count,
        public_https_request_count=accumulator.public_https_requests,
        dns_resolution_count=accumulator.dns_resolutions,
        robots_request_count=accumulator.robots_fetches,
        external_read_performed=plans[0].mode is PublicResearchPilotMode.OPERATOR_INVOKED_LIVE
        and accumulator.public_https_requests > 0,
        created_at=created_at,
        session_fingerprint=public_research_fingerprint(payload),
    )


def _single_header(headers: tuple[tuple[str, str], ...], name: str) -> str | None:
    values = [value for key, value in headers if key.lower() == name.lower()]
    if len(values) > 1:
        raise ValueError("duplicate_redirect_header")
    return values[0] if values else None


def _safe_reason_code(value: str) -> str:
    normalized = "".join(char if char.isalnum() else "_" for char in value.lower()).strip("_")
    return normalized[:80] or "public_research_policy_failure"


__all__ = ["ControlledPublicResearchPilot", "PIPELINE_PLANES"]
