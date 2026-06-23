from __future__ import annotations

from aion_brain.operator_console.data_sources import (
    DATA_SOURCE_MAP,
    list_console_views,
    view_data_sources,
)


def test_data_source_map_includes_module_lifecycle() -> None:
    keys = {spec.source_key for spec in DATA_SOURCE_MAP["module_lifecycle"]}

    assert "extensions" in keys
    assert "module_activation" in keys
    assert "module_mock_runtime" in keys


def test_data_source_map_includes_model_provider_hardening() -> None:
    keys = {spec.source_key for spec in DATA_SOURCE_MAP["model_provider_hardening"]}

    assert "model_provider_profiles" in keys
    assert "provider_readiness" in keys
    assert "provider_blockers" in keys


def test_view_data_sources_marks_missing_service_unavailable() -> None:
    sources = view_data_sources("overview", owner_scope=["workspace:main"], container=object())

    assert sources
    assert {source.available for source in sources} == {False}
    assert "module_lifecycle" in list_console_views()
