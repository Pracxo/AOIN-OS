"""Backup settings tests."""

from __future__ import annotations

from aion_brain.config import Settings


def test_backup_settings_defaults_match_env_example(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    for key in [
        "AION_BACKUPS_ENABLED",
        "AION_BACKUP_OUTPUT_DIR",
        "AION_BACKUP_DEFAULT_REDACTION_MODE",
        "AION_BACKUP_RESTORE_APPLY_ENABLED",
        "AION_BACKUP_MAX_RECORDS_PER_RESOURCE_DEFAULT",
        "AION_BACKUP_INCLUDE_VISUAL_TELEMETRY_DEFAULT",
    ]:
        monkeypatch.delenv(key, raising=False)

    settings = Settings(_env_file=None)  # type: ignore[call-arg]

    assert settings.backups_enabled is True
    assert settings.backup_output_dir == "artifacts/backups"
    assert settings.backup_default_redaction_mode == "redact_sensitive"
    assert settings.backup_restore_apply_enabled is False
    assert settings.backup_max_records_per_resource_default == 100000
    assert settings.backup_include_visual_telemetry_default is False


def test_backup_settings_read_environment_variables(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setenv("AION_BACKUPS_ENABLED", "false")
    monkeypatch.setenv("AION_BACKUP_OUTPUT_DIR", "artifacts/test-backups")
    monkeypatch.setenv("AION_BACKUP_DEFAULT_REDACTION_MODE", "metadata_only")
    monkeypatch.setenv("AION_BACKUP_RESTORE_APPLY_ENABLED", "true")
    monkeypatch.setenv("AION_BACKUP_MAX_RECORDS_PER_RESOURCE_DEFAULT", "25")
    monkeypatch.setenv("AION_BACKUP_INCLUDE_VISUAL_TELEMETRY_DEFAULT", "true")

    settings = Settings(_env_file=None)  # type: ignore[call-arg]

    assert settings.backups_enabled is False
    assert settings.backup_output_dir == "artifacts/test-backups"
    assert settings.backup_default_redaction_mode == "metadata_only"
    assert settings.backup_restore_apply_enabled is True
    assert settings.backup_max_records_per_resource_default == 25
    assert settings.backup_include_visual_telemetry_default is True
