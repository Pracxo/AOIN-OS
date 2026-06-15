from __future__ import annotations

import json
from typing import Any

from typer.testing import CliRunner

from aion_sdk.cli import main as cli_main
from aion_sdk.config import AIONClientConfig

runner = CliRunner()


class FakeBackups:
    def export(self, payload: dict[str, Any]) -> dict[str, object]:
        return {"backup_job_id": "backup-1", "dry_run": payload["dry_run"]}

    def validate(self, backup_job_id: str, scope: list[str]) -> dict[str, object]:
        return {"status": "passed", "backup_job_id": backup_job_id, "scope": scope}

    def validate_path(self, backup_path: str, scope: list[str]) -> dict[str, object]:
        return {"status": "passed", "backup_path": backup_path, "scope": scope}

    def restore_preview(self, payload: dict[str, Any]) -> dict[str, object]:
        return {"restore_preview_id": "preview-1", "backup_path": payload.get("backup_path")}

    def restore_apply(self, payload: dict[str, Any]) -> dict[str, object]:
        return {"restore_job_id": "restore-1", "mode": payload["mode"]}


class FakeClient:
    def __init__(self, config: AIONClientConfig) -> None:
        self.config = config
        self.backups = FakeBackups()


def _install_fake(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setattr(cli_main, "make_client", lambda config: FakeClient(config))


def _json(result) -> Any:  # type: ignore[no-untyped-def]
    return json.loads(result.stdout)


def test_cli_backups_export_defaults_to_dry_run(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    _install_fake(monkeypatch)

    result = runner.invoke(cli_main.app, ["--json", "backups", "export"])

    assert result.exit_code == 0
    assert _json(result)["backup_job_id"] == "backup-1"
    assert _json(result)["dry_run"] is True


def test_cli_backups_validate_path_works(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    _install_fake(monkeypatch)

    result = runner.invoke(
        cli_main.app,
        ["--json", "backups", "validate", "--path", "artifacts/backups/backup-1"],
    )

    assert result.exit_code == 0
    assert _json(result)["status"] == "passed"


def test_cli_restore_preview_and_apply_work(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    _install_fake(monkeypatch)

    preview = runner.invoke(
        cli_main.app,
        ["--json", "restore", "preview", "--backup-path", "artifacts/backups/backup-1"],
    )
    restore = runner.invoke(
        cli_main.app,
        ["--json", "restore", "apply", "--preview-id", "preview-1"],
    )

    assert preview.exit_code == 0
    assert restore.exit_code == 0
    assert _json(restore)["mode"] == "dry_run"
