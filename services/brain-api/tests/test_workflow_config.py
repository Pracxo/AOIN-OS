"""Workflow configuration tests."""

from aion_brain.config import Settings


def test_workflow_settings_default_to_local_disabled_execution() -> None:
    """Workflow defaults keep local execution explicit and Temporal disabled."""
    settings = Settings()

    assert settings.workflow_engine_adapter == "local"
    assert settings.workflow_local_worker_enabled is False
    assert settings.workflow_scheduler_enabled is False
    assert settings.temporal_enabled is False
    assert settings.temporal_namespace == "default"
    assert settings.temporal_task_queue == "aion-brain"
