"""Backup API tests."""

from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from aion_brain.api.backups import (
    get_backup_exporter,
    get_backup_validator,
    get_restore_preview_service,
    get_restore_service,
)
from aion_brain.contracts.scopes import ActorContext
from aion_brain.identity.dev_auth import get_actor_context
from aion_brain.main import app
from tests.backup_fakes import SCOPE, services


def test_backup_api_routes_work(tmp_path: Path) -> None:
    _, exporter, preview_service, restore_service, validator = services(tmp_path)
    app.dependency_overrides[get_backup_exporter] = lambda: exporter
    app.dependency_overrides[get_restore_preview_service] = lambda: preview_service
    app.dependency_overrides[get_restore_service] = lambda: restore_service
    app.dependency_overrides[get_backup_validator] = lambda: validator
    app.dependency_overrides[get_actor_context] = actor_context
    try:
        client = TestClient(app)
        created = client.post(
            "/brain/backups/export",
            json={"resource_types": ["events"], "dry_run": False},
        )
        backup_job_id = created.json()["backup_job_id"]
        backup_path = created.json()["output_dir"]
        fetched = client.get(f"/brain/backups/{backup_job_id}", params={"scope": SCOPE})
        listed = client.get("/brain/backups", params={"scope": SCOPE})
        validated = client.post(
            f"/brain/backups/{backup_job_id}/validate",
            params={"scope": SCOPE},
        )
        validated_path = client.post(
            "/brain/backups/validate-path",
            json={"backup_path": backup_path, "scope": SCOPE},
        )
        preview = client.post(
            "/brain/restore/preview",
            json={"backup_path": backup_path},
        )
        restore = client.post(
            "/brain/restore/apply",
            json={"restore_preview_id": preview.json()["restore_preview_id"]},
        )
        preview_get = client.get(
            f"/brain/restore/previews/{preview.json()['restore_preview_id']}",
            params={"scope": SCOPE},
        )
    finally:
        app.dependency_overrides.clear()

    assert [response.status_code for response in [
        created,
        fetched,
        listed,
        validated,
        validated_path,
        preview,
        restore,
        preview_get,
    ]] == [200, 200, 200, 200, 200, 200, 200, 200]
    assert restore.json()["status"] == "dry_run"


def actor_context() -> ActorContext:
    """Return dev actor context."""
    return ActorContext(
        actor_id="tester",
        actor_type="developer",
        workspace_id="main",
        roles=["owner"],
        permissions=["*"],
        security_scope=SCOPE,
        dev_mode=True,
    )
