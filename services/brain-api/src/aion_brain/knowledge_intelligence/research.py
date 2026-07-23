"""Controlled research acquisition orchestration."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timedelta

from aion_brain.contracts.knowledge_research import (
    CitationReference,
    ResearchFetchRequest,
    ResearchPlan,
    ResearchPlanOutcome,
    SourceCandidate,
    fingerprint_payload,
    reject_protected_material,
    sha256_bytes,
    utc_now,
)
from aion_brain.knowledge_intelligence.research_adapters import (
    DisabledResearchFetchAdapter,
    DisabledResearchSearchAdapter,
    ResearchAdapterDisabledError,
    ResearchFetchAdapter,
    ResearchSearchAdapter,
)
from aion_brain.knowledge_intelligence.research_budget import (
    ResearchBudgetDecision,
    ResearchResourceBudget,
    ResearchResourceUsage,
    evaluate_research_budget,
)
from aion_brain.knowledge_intelligence.research_evidence import (
    ResearchAcquisitionResult,
    ResearchDiagnostics,
    ResearchEvidenceBundle,
    ResearchIncidentRecord,
    ResearchOperatorReviewItem,
)
from aion_brain.knowledge_intelligence.research_policy import (
    ResearchDestinationResolver,
    canonicalize_research_url,
    decode_research_text,
    detect_untrusted_content_instruction_markers,
    host_is_allowlisted,
    parse_and_validate_content_type,
    project_safe_request_headers,
    project_safe_response_headers,
    validate_character_encoding,
    validate_domain_allowlist,
    validate_peer_matches_destination,
    validate_redirect_chain,
)
from aion_brain.knowledge_intelligence.source_deduplication import (
    build_lineage_records,
    deduplicate_source_snapshots,
)
from aion_brain.knowledge_intelligence.source_provenance import SourceProvenanceRecord
from aion_brain.knowledge_intelligence.source_snapshot import (
    EphemeralSourceArtifact,
    SourceSnapshot,
)


class ControlledResearchAcquisitionService:
    """Explicit operator-invoked acquisition service with no runtime registration."""

    def __init__(
        self,
        *,
        search_adapter: ResearchSearchAdapter | None = None,
        fetch_adapter: ResearchFetchAdapter | None = None,
        destination_resolver: ResearchDestinationResolver | None = None,
        resource_budget: ResearchResourceBudget | None = None,
        clock: Callable[[], datetime] = utc_now,
        monotonic_clock: Callable[[], float] | None = None,
        id_factory: Callable[[str, int], str] | None = None,
    ) -> None:
        self._search_adapter = search_adapter or DisabledResearchSearchAdapter()
        self._fetch_adapter = fetch_adapter or DisabledResearchFetchAdapter()
        self._destination_resolver = destination_resolver
        self._resource_budget = resource_budget or ResearchResourceBudget()
        self._clock = clock
        self._monotonic_clock = monotonic_clock or (lambda: 0.0)
        self._id_factory = id_factory or (lambda prefix, index: f"{prefix}-{index:04d}")

    def run(self, plan: ResearchPlan) -> ResearchAcquisitionResult:
        """Run one bounded acquisition plan and return redacted evidence."""

        started = self._clock()
        base_usage = ResearchResourceUsage(
            query_count=len(plan.queries),
            domain_count=len(plan.explicit_domain_allowlist),
            source_candidate_count=len(plan.explicit_source_candidates),
        )
        budget_decision = evaluate_research_budget(base_usage, self._resource_budget)
        if not budget_decision.within_budget:
            return self._stopped_result(
                plan,
                outcome="budget_blocked",
                budget_decision=budget_decision,
                created_at=started,
                reason_codes=("research_budget_exceeded", "research_plan_stopped_fail_closed"),
            )

        try:
            candidates = self._resolve_candidates(plan)
        except ResearchAdapterDisabledError:
            return self._stopped_result(
                plan,
                outcome="adapter_disabled",
                budget_decision=budget_decision,
                created_at=started,
                reason_codes=("research_adapter_disabled", "research_runtime_disabled"),
            )

        if not candidates:
            return self._stopped_result(
                plan,
                outcome="adapter_disabled",
                budget_decision=budget_decision,
                created_at=started,
                reason_codes=("research_adapter_disabled", "research_runtime_disabled"),
            )

        allowlist = validate_domain_allowlist(plan.explicit_domain_allowlist)
        snapshots: list[SourceSnapshot] = []
        artifacts: list[EphemeralSourceArtifact] = []
        provenance_records: list[SourceProvenanceRecord] = []
        citations: list[CitationReference] = []
        incidents: list[ResearchIncidentRecord] = []
        total_transfer = 0

        for index, candidate in enumerate(candidates, start=1):
            try:
                canonical = canonicalize_research_url(candidate.original_url)
                if not host_is_allowlisted(canonical.hostname, canonical.port, allowlist):
                    raise ValueError("research domain blocked")
                if candidate.robots_policy_status == "disallowed":
                    raise ValueError("robots policy disallowed")
                if not self._destination_resolver:
                    raise ValueError("destination resolver unavailable")
                destination = self._destination_resolver.resolve(canonical.hostname, canonical.port)
                headers = project_safe_request_headers(candidate.expected_content_types)
                request_id = self._id_factory("research-fetch-request", index)
                request_payload = {
                    "request_id": request_id,
                    "candidate_id": candidate.candidate_id,
                    "method": "GET",
                    "canonical_url": canonical.canonical_url,
                    "destination": destination.resolution_fingerprint,
                    "headers": headers,
                }
                request = ResearchFetchRequest(
                    request_id=request_id,
                    candidate_id=candidate.candidate_id,
                    method="GET",
                    canonical_url=canonical.canonical_url,
                    validated_destination=destination.model_dump(mode="json"),
                    safe_request_headers=headers,
                    timeout_seconds=self._resource_budget.maximum_timeout_seconds_per_request,
                    maximum_response_bytes=self._resource_budget.maximum_response_bytes_per_source,
                    maximum_redirects=self._resource_budget.maximum_redirects_per_fetch,
                    created_at=started,
                    fingerprint=fingerprint_payload(request_payload),
                )
                response = self._fetch_adapter.fetch(request)
                validate_peer_matches_destination(response.peer_address, destination)
                safe_headers = project_safe_response_headers(response.safe_response_headers)
                content_type = parse_and_validate_content_type(response.content_type)
                encoding = validate_character_encoding(content_type, response.character_encoding)
                if encoding is not None:
                    preview = decode_research_text(response.body[:512], encoding)
                else:
                    preview = ""
                reject_protected_material(preview, "source preview")
                markers = detect_untrusted_content_instruction_markers(response.body)
                if markers:
                    incidents.append(
                        self._incident(
                            plan.plan_id,
                            "research_prompt_injection_untrusted",
                            "Instruction-like content was marked untrusted.",
                            started,
                            index,
                        )
                    )
                total_transfer += response.body_length
                artifact = EphemeralSourceArtifact(
                    snapshot_id=self._id_factory("source-snapshot", index),
                    content_bytes=response.body,
                    content_sha256=sha256_bytes(response.body),
                )
                artifacts.append(artifact)
                redirect_fingerprint = validate_redirect_chain(())
                snapshot_payload = {
                    "snapshot_id": artifact.snapshot_id,
                    "plan_id": plan.plan_id,
                    "candidate_id": candidate.candidate_id,
                    "canonical_url": canonical.canonical_url,
                    "status_code": response.status_code,
                    "content_sha256": artifact.content_sha256,
                    "retrieval_timestamp": response.retrieved_at.isoformat(),
                }
                snapshot = SourceSnapshot(
                    snapshot_id=artifact.snapshot_id,
                    plan_id=plan.plan_id,
                    candidate_id=candidate.candidate_id,
                    query_ids=candidate.query_ids,
                    original_url_fingerprint=canonical.original_url_fingerprint,
                    canonical_url=canonical.canonical_url,
                    final_url=response.response_url,
                    method=request.method,
                    status_code=response.status_code,
                    content_type=content_type,
                    character_encoding=encoding,
                    content_length=response.body_length,
                    content_sha256=artifact.content_sha256,
                    safe_headers=safe_headers,
                    redirect_chain=(),
                    source_class=candidate.source_class,
                    robots_policy_status=candidate.robots_policy_status,
                    licence_policy_status=candidate.licence_policy_status,
                    publication_timestamp=None,
                    modification_timestamp=None,
                    retrieval_timestamp=response.retrieved_at,
                    content_artifact_id=f"artifact-{artifact.snapshot_id}",
                    content_present_in_memory=True,
                    redacted_preview=preview[:512],
                    snapshot_fingerprint=fingerprint_payload(snapshot_payload),
                )
                snapshots.append(snapshot)
                provenance = self._provenance(
                    snapshot,
                    canonical.canonical_url_fingerprint,
                    redirect_fingerprint,
                    destination.resolution_fingerprint,
                    fingerprint_payload(safe_headers),
                    started,
                    index,
                    plan.research_adapter_type,
                )
                provenance_records.append(provenance)
                citations.append(
                    self._citation(
                        snapshot,
                        canonical.canonical_url_fingerprint,
                        response.retrieved_at,
                        index,
                    )
                )
            except (ResearchAdapterDisabledError, ValueError, UnicodeDecodeError) as exc:
                incidents.append(
                    self._incident(
                        plan.plan_id,
                        "research_source_snapshot_rejected",
                        str(exc),
                        started,
                        index,
                    )
                )

        usage = ResearchResourceUsage(
            query_count=len(plan.queries),
            domain_count=len(plan.explicit_domain_allowlist),
            source_candidate_count=len(candidates),
            fetch_count=len(snapshots),
            maximum_response_bytes_for_any_source=max(
                (snapshot.content_length for snapshot in snapshots),
                default=0,
            ),
            total_transfer_bytes=total_transfer,
            snapshot_record_count=len(snapshots),
            maximum_safe_headers_for_any_snapshot=max(
                (len(snapshot.safe_headers) for snapshot in snapshots),
                default=0,
            ),
            maximum_citation_references_for_any_snapshot=1 if citations else 0,
            operator_review_item_count=1,
        )
        final_budget = evaluate_research_budget(usage, self._resource_budget)
        if not final_budget.within_budget:
            return self._stopped_result(
                plan,
                outcome="budget_blocked",
                budget_decision=final_budget,
                created_at=started,
                reason_codes=("research_budget_exceeded", "research_plan_stopped_fail_closed"),
            )

        dedup = deduplicate_source_snapshots(snapshots)
        lineage = build_lineage_records(snapshots, dedup, created_at=started)
        diagnostics = self._diagnostics(plan, snapshots, incidents, final_budget, started)
        review = self._review(plan, snapshots, citations, incidents, started)
        evidence_payload = {
            "plan_id": plan.plan_id,
            "snapshots": [snapshot.snapshot_fingerprint for snapshot in snapshots],
            "provenance": [record.provenance_fingerprint for record in provenance_records],
            "citations": [citation.citation_fingerprint for citation in citations],
            "lineage": [record.lineage_fingerprint for record in lineage],
            "incidents": [incident.fingerprint for incident in incidents],
        }
        bundle = ResearchEvidenceBundle(
            plan_id=plan.plan_id,
            snapshots=tuple(snapshots),
            provenance_records=tuple(provenance_records),
            citation_references=tuple(citations),
            lineage_records=lineage,
            deduplication_decisions=dedup,
            diagnostics=diagnostics,
            incidents=tuple(incidents),
            operator_review_items=(review,),
            created_at=started,
            fingerprint=fingerprint_payload(evidence_payload),
        )
        reason_codes = (
            "research_plan_completed",
            "research_source_snapshotted",
            "research_claim_verification_not_performed",
            "research_operator_review_required",
        )
        outcome: ResearchPlanOutcome
        if incidents:
            outcome = "completed_with_rejections"
        else:
            outcome = "completed"
        result_payload = {
            "plan_id": plan.plan_id,
            "outcome": outcome,
            "budget": final_budget.fingerprint,
            "evidence": bundle.fingerprint,
            "reason_codes": reason_codes,
        }
        _ = [artifact.purge() for artifact in artifacts]
        return ResearchAcquisitionResult(
            plan_id=plan.plan_id,
            outcome=outcome,
            budget_decision=final_budget,
            evidence_bundle=bundle,
            incidents=tuple(incidents),
            diagnostics=diagnostics,
            reason_codes=reason_codes,
            created_at=started,
            fingerprint=fingerprint_payload(result_payload),
        )

    def _resolve_candidates(self, plan: ResearchPlan) -> tuple[SourceCandidate, ...]:
        candidates = list(plan.explicit_source_candidates)
        if plan.search_adapter_type == "in_memory":
            for query in plan.queries:
                candidates.extend(
                    self._search_adapter.search(
                        query,
                        maximum_results=self._resource_budget.maximum_source_candidates_per_plan,
                    )
                )
        unique: dict[str, SourceCandidate] = {}
        for candidate in sorted(candidates, key=lambda item: item.candidate_id):
            canonical = canonicalize_research_url(candidate.original_url).canonical_url
            unique.setdefault(canonical, candidate)
        return tuple(unique.values())

    def _stopped_result(
        self,
        plan: ResearchPlan,
        *,
        outcome: ResearchPlanOutcome,
        budget_decision: ResearchBudgetDecision,
        created_at: datetime,
        reason_codes: tuple[str, ...],
    ) -> ResearchAcquisitionResult:
        diagnostics = ResearchDiagnostics(
            plan_id=plan.plan_id,
            reason_codes=reason_codes,
            bounded_counts={"snapshots": 0, "incidents": 0},
            adapter_state={
                "operator_invoked_http_adapter_policy_available": True,
                "system_http_transport_available": False,
                "public_network_fetch_available": False,
            },
            incident_ids=(),
            created_at=created_at,
            fingerprint=fingerprint_payload(
                {"plan_id": plan.plan_id, "reason_codes": reason_codes}
            ),
        )
        return ResearchAcquisitionResult(
            plan_id=plan.plan_id,
            outcome=outcome,
            budget_decision=budget_decision,
            evidence_bundle=None,
            incidents=(),
            diagnostics=diagnostics,
            reason_codes=reason_codes,
            created_at=created_at,
            fingerprint=fingerprint_payload(
                {"plan_id": plan.plan_id, "outcome": outcome, "reason_codes": reason_codes}
            ),
        )

    def _incident(
        self,
        plan_id: str,
        reason_code: str,
        summary: str,
        created_at: datetime,
        index: int,
    ) -> ResearchIncidentRecord:
        safe_summary = summary[:180] if "://" not in summary else "Source rejected by policy."
        payload = {
            "plan_id": plan_id,
            "reason_code": reason_code,
            "summary": safe_summary,
            "created_at": created_at.isoformat(),
        }
        return ResearchIncidentRecord(
            incident_id=self._id_factory("research-incident", index),
            plan_id=plan_id,
            severity="medium",
            reason_codes=(reason_code,),
            redacted_summary=safe_summary,
            created_at=created_at,
            fingerprint=fingerprint_payload(payload),
        )

    def _provenance(
        self,
        snapshot: SourceSnapshot,
        canonical_url_fingerprint: str,
        redirect_chain_fingerprint: str,
        destination_validation_fingerprint: str,
        safe_headers_fingerprint: str,
        created_at: datetime,
        index: int,
        adapter_type: str,
    ) -> SourceProvenanceRecord:
        payload = {
            "snapshot_id": snapshot.snapshot_id,
            "content_sha256": snapshot.content_sha256,
            "retrieval_timestamp": snapshot.retrieval_timestamp.isoformat(),
            "adapter_type": adapter_type,
        }
        return SourceProvenanceRecord(
            provenance_id=self._id_factory("source-provenance", index),
            snapshot_id=snapshot.snapshot_id,
            canonical_url_fingerprint=canonical_url_fingerprint,
            content_sha256=snapshot.content_sha256,
            source_class=snapshot.source_class,
            declared_author=None,
            declared_publisher=None,
            declared_title=None,
            declared_publication_timestamp=None,
            declared_modification_timestamp=None,
            retrieval_timestamp=snapshot.retrieval_timestamp,
            metadata_sources=("transport_headers",),
            robots_policy_status=snapshot.robots_policy_status,
            licence_policy_status=snapshot.licence_policy_status,
            redirect_chain_fingerprint=redirect_chain_fingerprint,
            destination_validation_fingerprint=destination_validation_fingerprint,
            safe_headers_fingerprint=safe_headers_fingerprint,
            adapter_type=adapter_type,  # type: ignore[arg-type]
            provenance_fingerprint=fingerprint_payload(payload),
        )

    def _citation(
        self,
        snapshot: SourceSnapshot,
        canonical_url_fingerprint: str,
        retrieved_at: datetime,
        index: int,
    ) -> CitationReference:
        payload = {
            "snapshot_id": snapshot.snapshot_id,
            "content_sha256": snapshot.content_sha256,
            "canonical_url_fingerprint": canonical_url_fingerprint,
            "retrieved_at": retrieved_at.isoformat(),
        }
        return CitationReference(
            citation_id=self._id_factory("citation-reference", index),
            snapshot_id=snapshot.snapshot_id,
            content_sha256=snapshot.content_sha256,
            canonical_url_fingerprint=canonical_url_fingerprint,
            locator_kind="full_source",
            locator_value="full_source_metadata_only",
            retrieval_timestamp=retrieved_at,
            citation_fingerprint=fingerprint_payload(payload),
        )

    def _diagnostics(
        self,
        plan: ResearchPlan,
        snapshots: list[SourceSnapshot],
        incidents: list[ResearchIncidentRecord],
        budget_decision: object,
        created_at: datetime,
    ) -> ResearchDiagnostics:
        payload = {
            "plan_id": plan.plan_id,
            "snapshot_count": len(snapshots),
            "incident_count": len(incidents),
            "budget": getattr(budget_decision, "fingerprint", ""),
        }
        return ResearchDiagnostics(
            plan_id=plan.plan_id,
            reason_codes=("research_claim_verification_not_performed", "research_runtime_disabled"),
            bounded_counts={"snapshots": len(snapshots), "incidents": len(incidents)},
            adapter_state={
                "operator_invoked_http_adapter_policy_available": True,
                "system_http_transport_available": False,
                "public_network_fetch_available": False,
            },
            incident_ids=tuple(incident.incident_id for incident in incidents),
            created_at=created_at,
            fingerprint=fingerprint_payload(payload),
        )

    def _review(
        self,
        plan: ResearchPlan,
        snapshots: list[SourceSnapshot],
        citations: list[CitationReference],
        incidents: list[ResearchIncidentRecord],
        created_at: datetime,
    ) -> ResearchOperatorReviewItem:
        distribution: dict[str, int] = {}
        for snapshot in snapshots:
            distribution[snapshot.source_class] = distribution.get(snapshot.source_class, 0) + 1
        payload = {
            "plan_id": plan.plan_id,
            "snapshots": [snapshot.snapshot_id for snapshot in snapshots],
            "citations": [citation.citation_id for citation in citations],
            "incidents": [incident.incident_id for incident in incidents],
        }
        return ResearchOperatorReviewItem(
            review_item_id=self._id_factory("research-review-item", 1),
            plan_id=plan.plan_id,
            snapshot_ids=tuple(snapshot.snapshot_id for snapshot in snapshots),
            source_class_distribution=distribution,
            policy_rejections=tuple(incident.redacted_summary for incident in incidents),
            budget_status="within_budget",
            lineage_summary={"snapshot_count": len(snapshots)},
            citation_reference_ids=tuple(citation.citation_id for citation in citations),
            incident_ids=tuple(incident.incident_id for incident in incidents),
            created_at=created_at,
            expires_at=created_at + timedelta(days=7),
            fingerprint=fingerprint_payload(payload),
        )


__all__ = ["ControlledResearchAcquisitionService"]
