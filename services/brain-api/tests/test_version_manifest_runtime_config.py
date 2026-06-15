"""Version manifest runtime config integration tests."""

from __future__ import annotations

from tests.kernel_fakes import kernel_container


def test_version_manifest_includes_config_hash() -> None:
    container = kernel_container()

    manifest = container.version_manifest_service.create_manifest(
        "0.1.0",
        "dev-user",
        ["workspace:main"],
    )

    assert manifest.metadata["config_hash"]
    assert "runtime_config.control_plane" in manifest.feature_flags
