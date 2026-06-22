"""Command consistency safety regression tests."""

from pathlib import Path

ROOT = Path(__file__).parents[1] / "src" / "aion_brain"
NEW_MODULES = [
    ROOT / "commands",
    ROOT / "idempotency",
    ROOT / "outbox",
    ROOT / "inbox",
    ROOT / "consistency",
]


def test_no_background_processor_starts() -> None:
    """The v0.1 consistency layer has no automatic processor loop."""
    text = _source_text()

    assert "while True" not in text
    assert "create_task(" not in text
    assert "start_background" not in text


def test_no_external_network_call_occurs() -> None:
    """The new layer does not import network client packages."""
    text = _source_text()

    assert "import requests" not in text
    assert "import httpx" not in text
    assert "from nats" not in text


def test_no_shell_execution_occurs() -> None:
    """The new layer does not execute shell commands."""
    text = _source_text()

    assert "subprocess" not in text
    assert "os.system" not in text


def test_no_domain_specific_logic_exists() -> None:
    """The command consistency layer remains domain-neutral."""
    text = _source_text().lower()

    for term in ["finance", "trading", "legal", "healthcare", "procurement"]:
        assert term not in text


def _source_text() -> str:
    chunks: list[str] = []
    for directory in NEW_MODULES:
        for path in directory.rglob("*.py"):
            chunks.append(path.read_text())
    return "\n".join(chunks)
