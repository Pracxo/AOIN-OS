"""Effect construction and comparison for simulation-only tool verification."""

from __future__ import annotations

from aion_brain.contracts.knowledge_tool_verification import (
    ToolEffectType,
    ToolExpectedEffect,
    ToolForbiddenEffect,
    forbidden_runtime_effects,
    tool_effect_fingerprint,
)


def build_expected_effect(
    *,
    effect_id: str,
    effect_type: ToolEffectType,
    effect_scope: str,
    artifact_id: str | None = None,
) -> ToolExpectedEffect:
    """Build a fingerprinted expected effect."""

    payload = {
        "schema_version": "aion-knowledge-tool-effect/v1",
        "effect_id": effect_id,
        "effect_type": effect_type,
        "effect_scope": effect_scope,
        "artifact_id": artifact_id,
        "requires_actual_execution": False,
        "requires_persistent_write": False,
        "synthetic": True,
        "runtime_effect": False,
    }
    return ToolExpectedEffect.model_validate(
        {**payload, "effect_fingerprint": tool_effect_fingerprint(payload)}
    )


def build_forbidden_effect(
    *,
    effect_id: str,
    effect_type: ToolEffectType,
    effect_scope: str,
    reason_code: str = "tool_actual_execution_blocked",
) -> ToolForbiddenEffect:
    """Build a fingerprinted forbidden effect."""

    payload = {
        "schema_version": "aion-knowledge-tool-effect/v1",
        "effect_id": effect_id,
        "effect_type": effect_type,
        "effect_scope": effect_scope,
        "reason_code": reason_code,
    }
    return ToolForbiddenEffect.model_validate(
        {**payload, "effect_fingerprint": tool_effect_fingerprint(payload)}
    )


def default_forbidden_runtime_effects() -> tuple[ToolForbiddenEffect, ...]:
    """Return the AION-215 runtime effects that simulation must never observe."""

    return tuple(
        build_forbidden_effect(
            effect_id=f"forbidden-{effect.value}",
            effect_type=effect,
            effect_scope="runtime-boundary",
            reason_code="tool_actual_execution_blocked",
        )
        for effect in sorted(forbidden_runtime_effects(), key=lambda item: item.value)
    )


def compare_simulated_effects(
    *,
    expected: tuple[ToolExpectedEffect, ...],
    forbidden: tuple[ToolForbiddenEffect, ...],
    observed: tuple[ToolExpectedEffect, ...],
) -> tuple[bool, bool, tuple[str, ...]]:
    """Compare observed synthetic effects against expected and forbidden effects."""

    expected_types = {item.effect_type for item in expected}
    observed_types = {item.effect_type for item in observed}
    forbidden_types = {item.effect_type for item in forbidden}
    expected_satisfied = expected_types.issubset(observed_types)
    forbidden_absent = observed_types.isdisjoint(forbidden_types)
    reason_codes: list[str] = []
    reason_codes.append(
        "tool_effect_expected_matched" if expected_satisfied else "tool_synthetic_simulation_failed"
    )
    reason_codes.append(
        "tool_effect_forbidden_absent" if forbidden_absent else "tool_effect_forbidden_detected"
    )
    return expected_satisfied, forbidden_absent, tuple(reason_codes)


__all__ = [
    "build_expected_effect",
    "build_forbidden_effect",
    "compare_simulated_effects",
    "default_forbidden_runtime_effects",
]
