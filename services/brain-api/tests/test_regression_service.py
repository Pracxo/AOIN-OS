"""Local regression service tests."""

from datetime import UTC, datetime

from aion_brain.contracts.policy import PolicyDecision, PolicyRequest
from aion_brain.contracts.regression import RegressionCaseCreateRequest, RegressionRunRequest
from aion_brain.contracts.replay import BrainSnapshot, ReplayRun
from aion_brain.regression.report import RegressionReportBuilder
from aion_brain.regression.service import RegressionService


class Policy:
    def authorize(self, request: PolicyRequest) -> PolicyDecision:
        return PolicyDecision(
            decision_id="decision-1",
            trace_id=request.trace_id or "",
            allow=True,
            approval_required=False,
            reason="allowed",
            constraints=[],
            audit_level="standard",
        )


class Repository:
    def __init__(self) -> None:
        self.cases = {}
        self.runs = {}

    def save_case(self, case):
        self.cases[case.case_id] = case
        return case

    def get_case(self, case_id):
        return self.cases.get(case_id)

    def list_cases(self, *, status=None, tags=None, limit=50):
        return [case for case in self.cases.values() if status is None or case.status == status][
            :limit
        ]

    def save_run(self, run):
        self.runs[run.regression_run_id] = run
        return run

    def get_run(self, regression_run_id):
        return self.runs.get(regression_run_id)


class Snapshots:
    def __init__(self) -> None:
        self.items = {}
        self.count = 0

    def with_actor_context(self, actor_context):
        return self

    def create_trace_snapshot(self, trace_id, snapshot_type, scope, created_by=None):
        self.count += 1
        item = BrainSnapshot(
            snapshot_id=f"snapshot-{self.count}",
            trace_id=trace_id,
            owner_scope=scope,
            snapshot_type=snapshot_type,
            state={"trace": {"outcome": {"status": "planned"}}},
            content_hash="hash",
        )
        self.items[item.snapshot_id] = item
        return item

    def get_snapshot(self, snapshot_id, scope):
        return self.items.get(snapshot_id)


class Replays:
    def __init__(self, snapshots: Snapshots) -> None:
        self.snapshots = snapshots

    def with_actor_context(self, actor_context):
        return self

    def replay(self, request):
        output = self.snapshots.create_trace_snapshot(
            "trace-replay", "replay_output", request.owner_scope
        )
        return ReplayRun(
            replay_id="replay-1",
            source_trace_id=request.source_trace_id,
            replay_trace_id="trace-replay",
            mode=request.mode,
            status="completed",
            input_snapshot_id=None,
            output_snapshot_id=output.snapshot_id,
            comparison={},
            drift_detected=False,
            created_by=None,
            created_at=datetime.now(UTC),
            completed_at=datetime.now(UTC),
        )


def test_regression_service_creates_case_and_counts_run() -> None:
    """Golden cases create snapshots and selected runs count pass/fail/drift."""
    repository = Repository()
    snapshots = Snapshots()
    service = RegressionService(
        repository,
        Replays(snapshots),
        snapshots,
        Policy(),
        None,
        RegressionReportBuilder(),
    )
    case = service.create_case(
        RegressionCaseCreateRequest(
            name="Stable planning",
            description="Generic golden trace.",
            source_trace_id="trace-1",
            owner_scope=["workspace:main"],
        )
    )
    run = service.run_regression(
        RegressionRunRequest(
            case_ids=[case.case_id],
            owner_scope=["workspace:main"],
        )
    )
    assert case.input_snapshot_id != case.expected_snapshot_id
    assert run.case_count == 1
    assert run.passed_count == 1
    assert run.failed_count == 0
    assert run.drift_count == 0
