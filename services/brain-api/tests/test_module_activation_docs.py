"""AION-083 module activation gate documentation tests."""

from pathlib import Path

from aion_brain.config import Settings
from aion_brain.policy_catalog.defaults import DEFAULT_ACTION_SPECS

ROOT = Path(__file__).resolve().parents[3]


def test_module_activation_docs_exist_and_are_indexed() -> None:
    for relative in [
        "docs/module-activation-gate.md",
        "docs/adr/0074-module-activation-request-gate.md",
    ]:
        assert (ROOT / relative).exists(), relative

    readme = _text("README.md")
    adr_index = _text("docs/adr/README.md")
    assert "docs/module-activation-gate.md" in readme
    assert "0074-module-activation-request-gate.md" in adr_index


def test_module_activation_settings_default_to_preview_only() -> None:
    settings = Settings(_env_file=None)

    assert settings.module_activation_requests_enabled is True
    assert settings.module_activation_gate_enabled is True
    assert settings.module_activation_execution_enabled is False
    assert settings.runtime_registration_enabled is False


def test_module_activation_policy_catalog_contains_gate_actions() -> None:
    action_names = {item[0] for item in DEFAULT_ACTION_SPECS}

    assert "module_activation.request.create" in action_names
    assert "module_activation.gate.run" in action_names
    assert "runtime.registration.preview.create" in action_names


def _text(relative: str) -> str:
    return (ROOT / relative).read_text()
