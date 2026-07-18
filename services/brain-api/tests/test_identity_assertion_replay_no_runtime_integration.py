from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def test_replay_core_adds_no_runtime_registration_surfaces() -> None:
    forbidden_paths = [
        "services/brain-api/src/aion_brain/api/identity_assertion_replay.py",
        "services/brain-api/src/aion_brain/api/identity_assertion.py",
        "services/brain-api/src/aion_brain/api/production_auth.py",
        "services/brain-api/src/aion_brain/api/request_identity.py",
        "services/brain-api/src/aion_brain/api/actor_context.py",
    ]
    for relative in forbidden_paths:
        assert not (ROOT / relative).exists(), relative

    untouched_sources = [
        "services/brain-api/src/aion_brain/config.py",
        "services/brain-api/src/aion_brain/kernel/app_factory.py",
        "services/brain-api/src/aion_brain/production_auth/request_middleware.py",
        "services/brain-api/src/aion_brain/production_auth/request_boundary.py",
        "services/brain-api/src/aion_brain/production_auth/actor_context.py",
    ]
    for relative in untouched_sources:
        text = (ROOT / relative).read_text()
        assert "IdentityAssertionReplay" not in text
        assert "identity_assertion_replay" not in text


def test_replay_source_has_no_scheduler_route_config_or_env_wiring() -> None:
    replay_sources = [
        "services/brain-api/src/aion_brain/production_auth/identity_assertion_replay.py",
        "services/brain-api/src/aion_brain/production_auth/identity_assertion_replay_repository.py",
        "services/brain-api/src/aion_brain/production_auth/identity_assertion_replay_service.py",
        "services/brain-api/src/aion_brain/production_auth/identity_assertion_pipeline.py",
    ]
    text = "\n".join((ROOT / relative).read_text() for relative in replay_sources)
    for forbidden in (
        "KernelContainer",
        "APIRouter",
        "FastAPI",
        "os.environ",
        "create_task",
        "threading.Thread",
        "startup",
        "shutdown",
        "click.",
    ):
        assert forbidden not in text
