from __future__ import annotations

from operator_console_integration_test_support import REPO_ROOT, operator_auth


def test_operator_console_source_scope_is_implemented_exactly():
    scope = operator_auth()["future_source_scope"]
    assert "services/brain-api/src/aion_brain/contracts/operator_console_integration.py" in scope
    assert all((REPO_ROOT / item).is_file() for item in scope)
    assert (REPO_ROOT / "operator-console-static/live-console.js").is_file()
    assert (REPO_ROOT / "scripts/operator-console-integrated-local-run.py").is_file()


def test_operator_console_prohibited_source_surfaces_remain_absent():
    prohibited = (
        "services/brain-api/src/aion_brain/operator_console_runtime/public_server.py",
        "services/brain-api/src/aion_brain/operator_console_runtime/network_client.py",
        "services/brain-api/src/aion_brain/operator_console_runtime/websocket.py",
        "services/brain-api/src/aion_brain/operator_console_runtime/event_stream.py",
        "services/brain-api/src/aion_brain/operator_console_runtime/cors.py",
        "services/brain-api/src/aion_brain/operator_console_runtime/credential_store.py",
        "services/brain-api/src/aion_brain/operator_console_runtime/token_store.py",
        "services/brain-api/src/aion_brain/operator_console_runtime/cookie_store.py",
        "services/brain-api/src/aion_brain/operator_console_runtime/browser_storage.py",
        "services/brain-api/src/aion_brain/operator_console_runtime/file_upload.py",
        "services/brain-api/src/aion_brain/operator_console_runtime/filesystem.py",
        "services/brain-api/src/aion_brain/operator_console_runtime/process_runtime.py",
        "services/brain-api/src/aion_brain/operator_console_runtime/background_worker.py",
        "services/brain-api/src/aion_brain/operator_console_runtime/scheduler.py",
    )
    assert not any((REPO_ROOT / item).exists() for item in prohibited)
