from __future__ import annotations

from datetime import UTC, datetime

from aion_brain.contracts.policy import PolicyDecision, PolicyRequest
from aion_brain.contracts.trace_narratives import TraceNarrativeRequest
from aion_brain.explanations.repository import ExplanationRepository
from aion_brain.explanations.trace_narrative import TraceNarrativeBuilder


class AllowPolicy:
    def authorize(self, request: PolicyRequest) -> PolicyDecision:
        return PolicyDecision(
            decision_id=f"decision-{request.request_id}",
            trace_id=request.trace_id or "",
            allow=True,
            approval_required=False,
            reason="allowed",
            constraints=[],
            audit_level="standard",
        )


class FakeAudit:
    def list_entries(
        self,
        *,
        trace_id: str | None = None,
        limit: int = 100,
        ascending: bool = True,
    ) -> list[dict[str, object]]:
        return [
            {
                "audit_entry_id": "audit-1",
                "trace_id": trace_id,
                "event_type": "policy_checked",
                "status": "completed",
                "created_at": datetime.now(UTC).isoformat(),
                "metadata": {"ascending": ascending, "limit": limit},
            }
        ]


def test_trace_narrative_builder_orders_public_timeline() -> None:
    builder = TraceNarrativeBuilder(
        ExplanationRepository(),
        AllowPolicy(),
        audit_ledger=FakeAudit(),
    )

    narrative = builder.build(
        TraceNarrativeRequest(
            trace_id="trace-1",
            owner_scope=["workspace:main"],
        )
    )

    assert narrative.status == "completed"
    assert narrative.timeline[0]["source"] == "audit_entries"
    assert builder.get(narrative.trace_narrative_id, ["workspace:main"]) is not None


def test_trace_narrative_builder_handles_missing_sections() -> None:
    builder = TraceNarrativeBuilder(ExplanationRepository(), AllowPolicy())

    narrative = builder.build(
        TraceNarrativeRequest(trace_id="trace-empty", owner_scope=["workspace:main"])
    )

    assert narrative.status == "insufficient_records"
    assert narrative.timeline == []
