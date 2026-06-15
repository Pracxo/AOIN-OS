"""Policy-gated local deterministic regression harness."""

from datetime import UTC, datetime
from typing import Any, Protocol, cast
from uuid import uuid4

from aion_brain.contracts.policy import PolicyRequest
from aion_brain.contracts.regression import (
    EvalAdapterRunRequest,
    EvalAdapterRunResult,
    RegressionCase,
    RegressionCaseCreateRequest,
    RegressionResultStatus,
    RegressionRun,
    RegressionRunRequest,
    RegressionRunResult,
)
from aion_brain.contracts.replay import ReplayRequest, TraceComparison
from aion_brain.contracts.scopes import ActorContext
from aion_brain.evaluation.adapters.base import EvaluationAdapter
from aion_brain.policy.base import PolicyAdapter
from aion_brain.policy.enrichment import PolicyInputEnricher
from aion_brain.regression.report import RegressionReportBuilder
from aion_brain.replay.comparator import TraceComparator
from aion_brain.replay.service import ReplayService
from aion_brain.replay.snapshot import ReplayPolicyDenied, SnapshotService, _emit


class RegressionPersistence(Protocol):
    """Regression persistence boundary."""

    def save_case(self, case: RegressionCase) -> RegressionCase: ...

    def get_case(self, case_id: str) -> RegressionCase | None: ...

    def list_cases(
        self,
        *,
        status: str | None = None,
        tags: list[str] | None = None,
        limit: int = 50,
    ) -> list[RegressionCase]: ...

    def save_run(self, run: RegressionRun) -> RegressionRun: ...

    def get_run(self, regression_run_id: str) -> RegressionRun | None: ...


class RegressionService:
    """Create golden cases and execute local deterministic regression runs."""

    def __init__(
        self,
        regression_repository: RegressionPersistence,
        replay_service: ReplayService,
        snapshot_service: SnapshotService,
        policy_adapter: PolicyAdapter,
        telemetry_service: object | None,
        report_builder: RegressionReportBuilder,
        comparator: TraceComparator | None = None,
        actor_context: ActorContext | None = None,
    ) -> None:
        self._repository = regression_repository
        self._replay_service = replay_service
        self._snapshot_service = snapshot_service
        self._policy_adapter = policy_adapter
        self._telemetry_service = telemetry_service
        self._report_builder = report_builder
        self._comparator = comparator or TraceComparator()
        self._actor_context = actor_context or ActorContext()

    def with_actor_context(self, actor_context: ActorContext) -> "RegressionService":
        """Return a request-scoped regression service."""
        return RegressionService(
            self._repository,
            self._replay_service.with_actor_context(actor_context),
            self._snapshot_service.with_actor_context(actor_context),
            self._policy_adapter,
            self._telemetry_service,
            self._report_builder,
            self._comparator,
            actor_context,
        )

    def create_case(self, request: RegressionCaseCreateRequest) -> RegressionCase:
        """Promote a completed trace into a golden local regression case."""
        case_id = request.case_id or f"case-{uuid4().hex}"
        self._authorize("regression.case.create", case_id, request.owner_scope, {})
        created_by = request.created_by or self._actor_context.actor_id
        input_snapshot = self._snapshot_service.create_trace_snapshot(
            request.source_trace_id,
            "regression_input",
            request.owner_scope,
            created_by,
        )
        expected_snapshot = self._snapshot_service.create_trace_snapshot(
            request.source_trace_id,
            "regression_expected",
            request.owner_scope,
            created_by,
        )
        case = self._repository.save_case(
            RegressionCase(
                case_id=case_id,
                name=request.name,
                description=request.description,
                source_trace_id=request.source_trace_id,
                input_snapshot_id=input_snapshot.snapshot_id,
                expected_snapshot_id=expected_snapshot.snapshot_id,
                owner_scope=request.owner_scope,
                status="active",
                tags=request.tags,
                metadata=request.metadata,
                created_by=created_by,
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
            )
        )
        _emit(
            self._telemetry_service,
            "regression_case_created",
            "regression",
            case.case_id,
            case.source_trace_id,
            case.owner_scope,
            0.5,
        )
        return case

    def get_case(self, case_id: str, scope: list[str]) -> RegressionCase | None:
        """Return an authorized in-scope regression case."""
        self._authorize("regression.case.read", case_id, scope, {})
        case = self._repository.get_case(case_id)
        if case is None or not set(case.owner_scope) & set(scope):
            return None
        return case

    def list_cases(
        self,
        scope: list[str],
        status: str | None = None,
        tags: list[str] | None = None,
        limit: int = 50,
    ) -> list[RegressionCase]:
        """Return authorized in-scope regression cases."""
        self._authorize("regression.case.read", None, scope, {})
        return [
            case
            for case in self._repository.list_cases(status=status, tags=tags, limit=limit)
            if set(case.owner_scope) & set(scope)
        ]

    def disable_case(self, case_id: str, reason: str) -> RegressionCase:
        """Disable a golden case without deleting its history."""
        case = self._repository.get_case(case_id)
        if case is None:
            raise LookupError("regression_case_not_found")
        self._authorize("regression.case.update", case_id, case.owner_scope, {})
        return self._repository.save_case(
            case.model_copy(
                update={
                    "status": "disabled",
                    "metadata": {**case.metadata, "disabled_reason": reason},
                    "updated_at": datetime.now(UTC),
                }
            )
        )

    def run_regression(self, request: RegressionRunRequest) -> RegressionRun:
        """Run selected active golden cases and persist a generic report."""
        run_id = request.regression_run_id or f"regression-{uuid4().hex}"
        try:
            self._authorize(
                "regression.run",
                run_id,
                request.owner_scope,
                {"mode": request.mode, "local": True},
            )
        except ReplayPolicyDenied:
            return self._repository.save_run(_blocked_run(run_id, request))

        _emit(
            self._telemetry_service,
            "regression_run_started",
            "regression",
            run_id,
            run_id,
            request.owner_scope,
            0.5,
        )
        cases = self._selected_cases(request)
        results = [self._run_case(run_id, case, request) for case in cases]
        passed = sum(result.status == "passed" for result in results)
        drift = sum(result.drift_detected for result in results)
        run = RegressionRun(
            regression_run_id=run_id,
            status="completed",
            case_count=len(results),
            passed_count=passed,
            failed_count=len(results) - passed,
            drift_count=drift,
            results=results,
            report=self._report_builder.build(results),
            created_by=request.created_by or self._actor_context.actor_id,
            created_at=datetime.now(UTC),
            completed_at=datetime.now(UTC),
        )
        stored = self._repository.save_run(run)
        _emit(
            self._telemetry_service,
            "regression_run_completed",
            "regression",
            run_id,
            run_id,
            request.owner_scope,
            0.8,
        )
        if drift:
            _emit(
                self._telemetry_service,
                "regression_drift_detected",
                "regression",
                run_id,
                run_id,
                request.owner_scope,
                1.0,
            )
        return stored

    def get_run(self, regression_run_id: str, scope: list[str]) -> RegressionRun | None:
        """Return a policy-authorized regression run."""
        self._authorize("regression.read", regression_run_id, scope, {})
        return self._repository.get_run(regression_run_id)

    def run_eval_adapter(
        self,
        request: EvalAdapterRunRequest,
        adapter: EvaluationAdapter,
    ) -> EvalAdapterRunResult:
        """Policy-gate and run an evaluation adapter boundary."""
        self._authorize(
            "eval.adapter.run",
            request.regression_run_id,
            self._actor_context.security_scope,
            {"adapter_name": request.adapter_name},
        )
        result = adapter.run(request)
        _emit(
            self._telemetry_service,
            "eval_adapter_run",
            "eval",
            request.regression_run_id or request.adapter_name,
            request.regression_run_id or "eval-local",
            self._actor_context.security_scope or ["workspace:main"],
            0.5,
        )
        return result

    def _selected_cases(self, request: RegressionRunRequest) -> list[RegressionCase]:
        cases = self._repository.list_cases(status="active", tags=request.tags, limit=1000)
        if request.case_ids:
            selected = set(request.case_ids)
            cases = [case for case in cases if case.case_id in selected]
        return [case for case in cases if set(case.owner_scope) & set(request.owner_scope)]

    def _run_case(
        self,
        run_id: str,
        case: RegressionCase,
        request: RegressionRunRequest,
    ) -> RegressionRunResult:
        replay = self._replay_service.replay(
            ReplayRequest(
                source_trace_id=case.source_trace_id,
                mode=request.mode,
                actor_id=request.created_by or self._actor_context.actor_id,
                workspace_id=self._actor_context.workspace_id,
                owner_scope=case.owner_scope,
                metadata={"regression_run_id": run_id, "case_id": case.case_id},
            )
        )
        expected = self._snapshot_service.get_snapshot(case.expected_snapshot_id, case.owner_scope)
        output = (
            self._snapshot_service.get_snapshot(replay.output_snapshot_id, case.owner_scope)
            if replay.output_snapshot_id
            else None
        )
        if expected is None or output is None:
            comparison = _failed_comparison(case.source_trace_id, replay.replay_trace_id)
            status = (
                "blocked_by_policy"
                if replay.status == "blocked_by_policy"
                else "replay_failed"
            )
        else:
            comparison = self._comparator.compare(expected, output)
            status = "passed" if not comparison.drift_detected else "failed"
        return RegressionRunResult(
            result_id=f"result-{uuid4().hex}",
            regression_run_id=run_id,
            case_id=case.case_id,
            replay_id=replay.replay_id,
            status=cast(RegressionResultStatus, status),
            drift_detected=comparison.drift_detected,
            comparison=comparison,
            created_at=datetime.now(UTC),
        )

    def _authorize(
        self,
        action_type: str,
        resource_id: str | None,
        scope: list[str],
        context: dict[str, Any],
    ) -> None:
        request = PolicyRequest(
            request_id=f"request-{uuid4().hex}",
            trace_id=self._actor_context.trace_id or resource_id,
            actor_id=self._actor_context.actor_id,
            workspace_id=self._actor_context.workspace_id,
            action_type=action_type,
            resource_type="regression",
            resource_id=resource_id,
            risk_level="low",
            approval_present=False,
            requested_permissions=[],
            security_scope=scope,
            context=context,
        )
        decision = self._policy_adapter.authorize(
            PolicyInputEnricher().enrich(request, self._actor_context)
        )
        if not decision.allow:
            raise ReplayPolicyDenied(decision)


def _blocked_run(run_id: str, request: RegressionRunRequest) -> RegressionRun:
    return RegressionRun(
        regression_run_id=run_id,
        status="blocked_by_policy",
        case_count=0,
        passed_count=0,
        failed_count=0,
        drift_count=0,
        results=[],
        report={"reason": "blocked_by_policy"},
        created_by=request.created_by,
        created_at=datetime.now(UTC),
        completed_at=datetime.now(UTC),
    )


def _failed_comparison(source_trace_id: str, replay_trace_id: str | None) -> TraceComparison:
    return TraceComparison(
        comparison_id=f"comparison-{uuid4().hex}",
        source_trace_id=source_trace_id,
        replay_trace_id=replay_trace_id,
        source_snapshot_id=None,
        replay_snapshot_id=None,
        matched=False,
        drift_detected=True,
        score=0.0,
        differences=[
            {
                "path": "state",
                "source": "expected_snapshot",
                "replay": None,
                "severity": "high",
                "reason": "required_section_missing",
            }
        ],
        ignored_fields=[],
        created_at=datetime.now(UTC),
    )
