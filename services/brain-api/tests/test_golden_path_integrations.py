"""Golden Path integration hook tests."""

from pathlib import Path
from types import SimpleNamespace

from aion_brain.freeze.gate import FreezeGateService
from aion_brain.operator.action_center import ActionCenterService
from aion_brain.release_package.packager import ReleasePackager


def test_freeze_gate_can_require_green_golden_path() -> None:
    service = object.__new__(FreezeGateService)
    service._golden_path_repository = _FakeGoldenPathRepository(ready=True)

    result = service._check_golden_path_passed()

    assert result["status"] == "passed"
    assert result["details"]["release_candidate_ready"] is True


def test_freeze_gate_fails_when_golden_path_report_not_ready() -> None:
    service = object.__new__(FreezeGateService)
    service._golden_path_repository = _FakeGoldenPathRepository(ready=False)

    result = service._check_golden_path_passed()

    assert result["status"] == "failed"


def test_release_packager_includes_golden_path_summary() -> None:
    packager = object.__new__(ReleasePackager)
    packager._golden_path_repository = _FakeGoldenPathRepository(ready=True)

    summary = packager._golden_path_summary(["workspace:main"])

    assert summary["available"] is True
    assert summary["release_candidate_ready"] is True
    assert summary["external_calls_allowed"] is False


def test_operator_action_center_builds_golden_path_items() -> None:
    service = ActionCenterService(
        repository=object(),  # type: ignore[arg-type]
        golden_path_repository=_FakeGoldenPathRepository(ready=False),
    )

    items = service._failed_golden_path_run_items(["workspace:main"])
    report_items = service._critical_golden_path_report_items(["workspace:main"])

    assert items[0].source_type == "golden_path_run"
    assert report_items[0].source_type == "golden_path_report"


def test_golden_path_does_not_add_frontend_dependencies() -> None:
    forbidden = {"react", "three", "rive", "lottie", "canvas"}
    root_dir = Path(__file__).resolve().parents[3]
    pyproject = (
        root_dir / "services/brain-api/pyproject.toml",
        root_dir / "packages/aion-sdk-python/pyproject.toml",
    )
    for path in pyproject:
        text = path.read_text(encoding="utf-8").lower()
        assert not any(f'"{name}' in text or f"'{name}" in text for name in forbidden)


class _FakeGoldenPathRepository:
    def __init__(self, *, ready: bool) -> None:
        self._ready = ready

    def latest_report(self) -> object:
        return SimpleNamespace(
            golden_path_report_id="report-1",
            golden_path_run_id="run-1",
            status="passed" if self._ready else "failed",
            readiness_score=1.0 if self._ready else 0.4,
            release_candidate_ready=self._ready,
            findings=[] if self._ready else [{"severity": "critical"}],
            owner_scope=["workspace:main"],
            trace_id="trace-1",
        )

    def latest_run(self) -> object:
        return SimpleNamespace(
            golden_path_run_id="run-1",
            status="dry_run" if self._ready else "failed",
            owner_scope=["workspace:main"],
            trace_id="trace-1",
        )

    def status(self, scope: list[str]) -> dict[str, object]:
        return {"status": "passed" if self._ready else "failed", "scope": scope}

    def list_runs(self, **kwargs: object) -> list[object]:
        status = kwargs.get("status")
        if status not in {"failed", "blocked"}:
            return []
        return [
            SimpleNamespace(
                golden_path_run_id=f"run-{status}",
                status=status,
                failed_count=1 if status == "failed" else 0,
                blocked_count=1 if status == "blocked" else 0,
                report_id="report-1",
                owner_scope=["workspace:main"],
                trace_id="trace-1",
            )
        ]

    def list_reports(self, **kwargs: object) -> list[object]:
        status = kwargs.get("status")
        if status != "failed":
            return []
        return [self.latest_report()]
