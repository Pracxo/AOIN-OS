"""Sleep consolidation service tests."""

from datetime import UTC, datetime

from aion_brain.contracts.cycles import CognitiveCycleRun
from aion_brain.cycles.sleep import SleepConsolidationService


class FakeWorkingMemory:
    """Working memory fake."""

    def __init__(self) -> None:
        self.swept = False

    def count_expired(self, scope: list[str], limit: int) -> int:
        return min(limit, len(scope))

    def sweep_expired(self, scope: list[str], limit: int) -> dict[str, int]:
        self.swept = True
        return {"swept": min(limit, len(scope))}


class FakeDecay:
    """Memory decay fake."""

    def recompute_decay(
        self,
        scope: list[str],
        memory_types: list[str],
        limit: int,
        dry_run: bool,
    ) -> dict[str, object]:
        return {"decayed": min(limit, 2), "dry_run": dry_run}


class FakeConflicts:
    """Conflict scan fake."""

    def scan(self, request: object) -> list[object]:
        return [object(), object()]


class FakeCompaction:
    """Compaction fake."""

    def compact(self, request: object) -> dict[str, object]:
        return {"compacted": True}


class FakeSkillService:
    """Skill candidate fake."""

    def create_candidate_from_cycle(self, cycle_run: CognitiveCycleRun) -> list[str]:
        return ["candidate-1"]


class FakeRepository:
    """Sleep record repository fake."""

    def __init__(self) -> None:
        self.saved: list[object] = []

    def save_sleep_record(self, record: object) -> object:
        self.saved.append(record)
        return record


def make_cycle_run(**input_values: object) -> CognitiveCycleRun:
    """Create a cycle run contract."""
    return CognitiveCycleRun(
        cycle_run_id="cycle-run-1",
        trace_id="trace-1",
        actor_id="actor-1",
        workspace_id="workspace-1",
        cycle_type="sleep_consolidation",
        status="running",
        mode="dry_run",
        owner_scope=["workspace:main"],
        steps=[],
        input=dict(input_values),
        output={},
        error={},
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


def test_sleep_consolidation_dry_run_avoids_mutation() -> None:
    """Dry-run consolidation previews work and persists the record."""
    working_memory = FakeWorkingMemory()
    repository = FakeRepository()
    service = SleepConsolidationService(
        working_memory_service=working_memory,
        memory_decay_service=FakeDecay(),
        memory_conflict_service=FakeConflicts(),
        memory_compaction_service=FakeCompaction(),
        cycle_repository=repository,
    )

    record = service.run(make_cycle_run(), dry_run=True)

    assert record.working_memory_slots_reviewed == 1
    assert record.memories_decayed == 2
    assert record.conflicts_detected == 2
    assert record.skill_candidates_created == 0
    assert record.result["dry_run"] is True
    assert record.result["skill_promotion"] == "not_performed"
    assert working_memory.swept is False
    assert repository.saved == [record]


def test_sleep_consolidation_creates_skill_candidates_only_when_explicit() -> None:
    """Skill candidates need explicit input and still never promote skills."""
    service = SleepConsolidationService(
        working_memory_service=FakeWorkingMemory(),
        skill_service=FakeSkillService(),
        cycle_repository=FakeRepository(),
    )

    record = service.run(make_cycle_run(create_skill_candidates=True), dry_run=False)

    assert record.skill_candidates_created == 1
    assert record.result["skill_promotion"] == "not_performed"
