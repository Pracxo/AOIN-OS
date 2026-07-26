"""Controlled deterministic tool verification fabric for AION-215."""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

from aion_brain.contracts.knowledge_research import utc_now
from aion_brain.contracts.knowledge_tool_verification import (
    ToolFindingSeverity,
    ToolManifestRegistrySnapshot,
    ToolSessionOutcome,
    ToolVerificationFixtureEnvelope,
    ToolVerificationIncident,
    ToolVerificationQuery,
    ToolVerificationQueryResult,
    ToolVerificationResourceUsage,
    ToolVerificationSession,
    ToolVerificationStatus,
    tool_query_fingerprint,
    tool_query_result_fingerprint,
    tool_session_fingerprint,
)
from aion_brain.knowledge_intelligence.tool_attestation import build_attestation_chain
from aion_brain.knowledge_intelligence.tool_evidence import (
    build_evidence_bundle,
    build_operator_review_item,
    build_tool_diagnostics,
    build_tool_incident,
)
from aion_brain.knowledge_intelligence.tool_integrity import audit_tool_verification_session
from aion_brain.knowledge_intelligence.tool_manifests import (
    InMemoryToolManifestRegistry,
    build_default_tool_manifest_registry,
)
from aion_brain.knowledge_intelligence.tool_planning import build_tool_plan
from aion_brain.knowledge_intelligence.tool_simulation import (
    ExplicitLocalToolVerificationFixtureReplay,
    SyntheticToolSimulator,
)
from aion_brain.knowledge_intelligence.tool_verification import (
    build_default_verification_rules,
    build_default_verifier_profiles,
    verify_tool_plan_and_simulation,
)


class InMemoryToolVerificationSessionRepository:
    """Per-instance in-memory session repository with no persistence backend."""

    def __init__(self, sessions: Iterable[ToolVerificationSession] = ()) -> None:
        self._sessions = {session.session_id: session for session in sessions}

    def add(self, session: ToolVerificationSession) -> None:
        """Store one immutable session in this in-memory instance."""

        self._sessions[session.session_id] = session

    def snapshot(self) -> tuple[ToolVerificationSession, ...]:
        """Return deterministic immutable session snapshot."""

        return tuple(self._sessions[key] for key in sorted(self._sessions))

    def reject_persistent_write(self, payload: object | None = None) -> ToolSessionOutcome:
        """Reject any request to write tool verification state persistently."""

        _ = payload
        return ToolSessionOutcome.PERSISTENT_WRITE_DISABLED


class ControlledToolVerificationFabric:
    """Pure in-memory deterministic fabric that plans, simulates, verifies, and attests."""

    def __init__(
        self,
        *,
        registry: InMemoryToolManifestRegistry | None = None,
        repository: InMemoryToolVerificationSessionRepository | None = None,
        clock: object = utc_now,
        repository_root: Path | None = None,
    ) -> None:
        self.registry = registry or build_default_tool_manifest_registry()
        self.repository = repository or InMemoryToolVerificationSessionRepository()
        self.clock = clock
        self.repository_root = repository_root or Path.cwd()

    def run_session(
        self,
        *,
        intent_id: str = "intent-aion-215-001",
        registry_snapshot: ToolManifestRegistrySnapshot | None = None,
        fixture: ToolVerificationFixtureEnvelope | None = None,
    ) -> ToolVerificationSession:
        """Run a complete deterministic simulation-only verification session."""

        from aion_brain.knowledge_intelligence.tool_planning import build_tool_intent

        snapshot = registry_snapshot or self.registry.snapshot()
        intent = fixture.intent if fixture is not None else build_tool_intent(intent_id=intent_id)
        plan = build_tool_plan(intent=intent, registry=snapshot)
        simulation = SyntheticToolSimulator(snapshot).simulate(plan, fixture=fixture)
        preliminary_usage = ToolVerificationResourceUsage(
            tool_manifests=len(snapshot.manifests),
            tool_candidates=len(plan.candidates),
            tool_steps=len(plan.steps),
            output_artifacts=len(simulation.artifacts),
            simulated_sessions=1,
            fixture_records=len(fixture.fixture_records) if fixture is not None else 0,
        )
        profiles = build_default_verifier_profiles()
        rules = build_default_verification_rules(plan.required_verifier_roles)
        findings = verify_tool_plan_and_simulation(
            plan=plan,
            simulation=simulation,
            profiles=profiles,
            rules=rules,
            usage=preliminary_usage,
        )
        attestations = build_attestation_chain(findings, clock=self.clock)
        usage = ToolVerificationResourceUsage(
            tool_manifests=len(snapshot.manifests),
            tool_candidates=len(plan.candidates),
            tool_steps=len(plan.steps),
            output_artifacts=len(simulation.artifacts),
            attestations=len(attestations),
            simulated_sessions=1,
            fixture_records=len(fixture.fixture_records) if fixture is not None else 0,
        )
        all_findings_passed = all(finding.passed for finding in findings)
        if simulation.status is not ToolVerificationStatus.SIMULATION_PASSED:
            outcome = ToolSessionOutcome.SIMULATION_FAILED
        elif not all_findings_passed:
            outcome = ToolSessionOutcome.VERIFICATION_FAILED
        else:
            outcome = ToolSessionOutcome.SIMULATION_PASSED
        session_id = f"session-{intent.intent_id}"
        diagnostics = build_tool_diagnostics(
            diagnostic_id=f"diagnostic-{session_id}",
            reason_codes=("tool_synthetic_simulation_passed", "tool_operator_review_required"),
            summary="Synthetic tool simulation completed with runtime and persistence disabled.",
        )
        incidents: tuple[ToolVerificationIncident, ...] = ()
        if outcome is not ToolSessionOutcome.SIMULATION_PASSED:
            incidents = (
                build_tool_incident(
                    incident_id=f"incident-{session_id}",
                    severity=ToolFindingSeverity.ERROR,
                    reason_codes=("tool_synthetic_simulation_failed",),
                    redacted_detail="Synthetic verification failed without executing any tool.",
                ),
            )
        operator_review_items = (
            build_operator_review_item(
                review_item_id=f"operator-review-{session_id}",
                session_id=session_id,
            ),
        )
        evidence_bundle = build_evidence_bundle(
            evidence_id=f"evidence-{session_id}",
            session_id=session_id,
            simulation=simulation,
            findings=findings,
            attestations=attestations,
        )
        payload = {
            "schema_version": "aion-knowledge-tool-verification-session/v1",
            "program_id": "AION-KNOWLEDGE-INTELLIGENCE-001",
            "authorization_transaction_id": "AION-214-KI-0006",
            "implementation_task": "AION-215",
            "formal_closeout_task": "AION-216",
            "session_id": session_id,
            "registry_snapshot": snapshot,
            "intent": intent,
            "plan": plan,
            "simulation": simulation,
            "findings": findings,
            "attestations": attestations,
            "diagnostics": diagnostics,
            "incidents": incidents,
            "operator_review_items": operator_review_items,
            "evidence_bundle": evidence_bundle,
            "resource_usage": usage,
            "overall_status": outcome,
            "explicit_abstention": True,
            "operator_review_required": True,
            "tool_verification_fabric_authorized": True,
            "tool_verification_fabric_implemented": True,
            "tool_verification_fabric_state": (
                "implemented_deterministic_simulation_verification_attestation_"
                "persistent_write_disabled"
            ),
            "tool_verification_fabric_runtime_enabled": False,
            "actual_tool_execution_enabled": False,
            "actual_tool_executed": False,
            "persistent_tool_state_write_enabled": False,
            "persistent_write_applied": False,
            "knowledge_promoted": False,
            "belief_mutated": False,
            "synthetic": True,
            "read_only": True,
            "redacted": True,
            "runtime_effect": False,
        }
        session = ToolVerificationSession.model_validate(
            {**payload, "session_fingerprint": tool_session_fingerprint(payload)}
        )
        self.repository.add(session)
        return session

    def replay_fixture(self, path: Path) -> ToolVerificationSession:
        """Replay an explicit local fixture without creating persistent state."""

        replay = ExplicitLocalToolVerificationFixtureReplay(repository_root=self.repository_root)
        fixture = replay.load_fixture(path)
        return self.run_session(registry_snapshot=fixture.registry_snapshot, fixture=fixture)

    def reject_persistent_write(self, payload: object | None = None) -> ToolSessionOutcome:
        """Reject persistent tool-state write attempts."""

        return self.repository.reject_persistent_write(payload)

    def query(self, query: ToolVerificationQuery) -> ToolVerificationQueryResult:
        """Run a bounded exact query over in-memory sessions."""

        matches: list[ToolVerificationSession] = []
        for session in self.repository.snapshot():
            if query.session_id is not None and session.session_id != query.session_id:
                continue
            if query.intent_id is not None and session.intent.intent_id != query.intent_id:
                continue
            if query.plan_id is not None and session.plan.plan_id != query.plan_id:
                continue
            if (
                query.overall_status is not None
                and session.overall_status is not query.overall_status
            ):
                continue
            matches.append(session)
            if len(matches) >= query.limit:
                break
        sessions = tuple(matches)
        payload = {
            "schema_version": "aion-knowledge-tool-verification-query/v1",
            "query": query,
            "sessions": sessions,
            "result_count": len(sessions),
        }
        return ToolVerificationQueryResult.model_validate(
            {**payload, "query_result_fingerprint": tool_query_result_fingerprint(payload)}
        )

    def query_by_session_id(self, session_id: str) -> ToolVerificationQueryResult:
        """Convenience exact query by session id."""

        payload = {
            "schema_version": "aion-knowledge-tool-verification-query/v1",
            "session_id": session_id,
            "intent_id": None,
            "plan_id": None,
            "overall_status": None,
            "limit": 100,
        }
        query = ToolVerificationQuery.model_validate(
            {**payload, "query_fingerprint": tool_query_fingerprint(payload)}
        )
        return self.query(query)

    def audit_last_session(self) -> object:
        """Audit the latest in-memory session."""

        sessions = self.repository.snapshot()
        if not sessions:
            raise ValueError("no tool verification session to audit")
        return audit_tool_verification_session(sessions[-1])


__all__ = [
    "ControlledToolVerificationFabric",
    "InMemoryToolVerificationSessionRepository",
]
