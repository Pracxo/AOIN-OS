"""Reflection and skill safety guardrail tests."""

from pathlib import Path


def test_learning_logic_does_not_modify_source_or_execute_dynamic_code() -> None:
    """Reflection and skill learning stores data, not generated executable code."""
    root = Path(__file__).resolve().parents[1] / "src" / "aion_brain"
    sources = [
        root / "reflection" / "engine.py",
        root / "skills" / "promotion.py",
        root / "skills" / "service.py",
        root / "skills" / "matcher.py",
    ]
    combined = "\n".join(path.read_text() for path in sources)

    forbidden = [
        "exec(",
        "eval(",
        "subprocess",
        "os.system",
        "write_text(",
        "open(",
        "compile(",
        "model.complete",
        "openai",
        "anthropic",
    ]

    assert all(token not in combined for token in forbidden)
