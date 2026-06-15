"""PromptBuilder evidence reference tests."""

from aion_brain.contracts.context import ContextPacket
from aion_brain.contracts.reasoning import ReasoningRequest
from aion_brain.reasoning.prompt_builder import PromptBuilder


def test_prompt_builder_includes_evidence_refs() -> None:
    """Prompt packets carry evidence refs from context."""
    request = ReasoningRequest(
        reasoning_id="reasoning-1",
        trace_id="trace-1",
        intent=None,
        context=ContextPacket(
            context_id="context-1",
            intent_id="intent-1",
            goal="answer",
            known_context=[{"source": "evidence_vault", "evidence_ref": "evidence-1"}],
            retrieved_memory_ids=[],
            available_capability_ids=[],
            constraints=[],
            open_questions=[],
            execution_limits={},
        ),
        mode="analyze",
        risk_level="low",
        metadata={},
    )

    prompt = PromptBuilder().build(request)
    items = {item["type"]: item["value"] for item in prompt.context_items}

    assert items["evidence_refs"] == ["evidence-1"]
    assert any("Ground claims" in instruction for instruction in prompt.system_instructions)

