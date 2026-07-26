"""Deterministic synthetic dry-run simulation for AION-215 tool plans."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from aion_brain.contracts.knowledge_research import fingerprint_payload
from aion_brain.contracts.knowledge_tool_verification import (
    AUTHORIZATION_TRANSACTION_ID,
    FORMAL_CLOSEOUT_TASK,
    IMPLEMENTATION_TASK,
    MAXIMUM_FIXTURE_BYTES,
    PROGRAM_ID,
    ToolInvocationPlan,
    ToolManifestRegistrySnapshot,
    ToolSimulationArtifact,
    ToolSimulationResult,
    ToolVerificationError,
    ToolVerificationFixtureEnvelope,
    ToolVerificationStatus,
    tool_artifact_fingerprint,
    tool_fixture_fingerprint,
    tool_simulation_fingerprint,
)
from aion_brain.knowledge_intelligence.tool_effects import compare_simulated_effects


def assert_tool_fixture_path_allowed(path: Path, *, repository_root: Path) -> Path:
    """Validate explicit local fixture path constraints."""

    text = str(path)
    if "://" in text or text.startswith("~") or "$" in text:
        raise ToolVerificationError("tool fixture path syntax rejected")
    if not path.is_absolute():
        raise ToolVerificationError("tool fixture path must be absolute")
    if any(part.startswith(".") for part in path.parts[1:]):
        raise ToolVerificationError("hidden tool fixture path rejected")
    if path.is_symlink():
        raise ToolVerificationError("tool fixture symlink rejected")
    if not path.is_file():
        raise ToolVerificationError("tool fixture must be a regular file")
    resolved = path.resolve()
    root = repository_root.resolve()
    if resolved == root or root in resolved.parents:
        raise ToolVerificationError("tool fixture path inside repository rejected")
    if resolved.stat().st_size > MAXIMUM_FIXTURE_BYTES:
        raise ToolVerificationError("tool fixture byte limit exceeded")
    return resolved


def build_tool_fixture_envelope(
    *,
    registry_snapshot: ToolManifestRegistrySnapshot,
    intent_id_prefix: str = "fixture",
    fixture_records: tuple[dict[str, Any], ...] = (),
) -> ToolVerificationFixtureEnvelope:
    """Build a fixture envelope around the first deterministic default intent."""

    from aion_brain.knowledge_intelligence.tool_planning import build_tool_intent

    intent = build_tool_intent(intent_id=f"intent-{intent_id_prefix}-001")
    payload = {
        "schema_version": "aion-knowledge-tool-verification-fixture/v1",
        "program_id": PROGRAM_ID,
        "authorization_transaction_id": AUTHORIZATION_TRANSACTION_ID,
        "implementation_task": IMPLEMENTATION_TASK,
        "formal_closeout_task": FORMAL_CLOSEOUT_TASK,
        "registry_snapshot": registry_snapshot,
        "intent": intent,
        "fixture_records": fixture_records,
        "synthetic": True,
        "read_only": True,
        "redacted": True,
        "persistent_write_applied": False,
        "runtime_effect": False,
    }
    return ToolVerificationFixtureEnvelope.model_validate(
        {**payload, "fixture_fingerprint": tool_fixture_fingerprint(payload)}
    )


class ExplicitLocalToolVerificationFixtureReplay:
    """Read one explicit local synthetic fixture outside the repository."""

    def __init__(self, *, repository_root: Path) -> None:
        self.repository_root = repository_root

    def load_fixture(self, path: Path) -> ToolVerificationFixtureEnvelope:
        """Load and validate a fixture envelope without mutating state."""

        fixture_path = assert_tool_fixture_path_allowed(path, repository_root=self.repository_root)
        try:
            payload_text = fixture_path.read_text(encoding="utf-8")
        except UnicodeDecodeError as exc:
            raise ToolVerificationError("tool fixture must be valid UTF-8") from exc
        try:
            payload = json.loads(payload_text)
        except json.JSONDecodeError as exc:
            raise ToolVerificationError("tool fixture JSON rejected") from exc
        if not isinstance(payload, dict):
            raise ToolVerificationError("tool fixture envelope must be an object")
        if len(payload_text.encode("utf-8")) > MAXIMUM_FIXTURE_BYTES:
            raise ToolVerificationError("tool fixture byte limit exceeded")
        return ToolVerificationFixtureEnvelope.model_validate(payload)


class SyntheticToolSimulator:
    """Pure deterministic simulator that never calls a real tool."""

    def __init__(self, registry_snapshot: ToolManifestRegistrySnapshot) -> None:
        self.registry_snapshot = registry_snapshot

    def simulate(
        self,
        plan: ToolInvocationPlan,
        *,
        fixture: ToolVerificationFixtureEnvelope | None = None,
    ) -> ToolSimulationResult:
        """Produce a canonical synthetic dry-run result."""

        step = plan.steps[0]
        manifest = next(
            item
            for item in self.registry_snapshot.manifests
            if item.manifest_id == step.manifest_id
        )
        input_fingerprint = fingerprint_payload(step.input_payload)
        canonical_output: dict[str, Any] = {
            "input_fingerprint": input_fingerprint,
            "plan_id": plan.plan_id,
            "status": "synthetic_simulation_only",
            "tool_id": manifest.tool_id,
            "validated": True,
        }
        if fixture is not None:
            canonical_output["fixture_fingerprint"] = fixture.fixture_fingerprint
            canonical_output["fixture_record_count"] = len(fixture.fixture_records)
        output_fingerprint = fingerprint_payload(canonical_output)
        artifact_payload = {
            "schema_version": "aion-knowledge-tool-simulation-artifact/v1",
            "artifact_id": f"artifact-{step.step_id}-001",
            "step_id": step.step_id,
            "output_schema_id": manifest.output_schema.schema_id,
            "canonical_output": canonical_output,
            "output_fingerprint": output_fingerprint,
            "synthetic": True,
            "redacted": True,
            "runtime_effect": False,
        }
        artifact = ToolSimulationArtifact.model_validate(
            {
                **artifact_payload,
                "artifact_fingerprint": tool_artifact_fingerprint(artifact_payload),
            }
        )
        expected_satisfied, forbidden_absent, effect_reason_codes = compare_simulated_effects(
            expected=step.expected_effects,
            forbidden=step.forbidden_effects,
            observed=step.expected_effects,
        )
        status = (
            ToolVerificationStatus.SIMULATION_PASSED
            if expected_satisfied and forbidden_absent
            else ToolVerificationStatus.SIMULATION_FAILED
        )
        reason_codes = tuple(
            dict.fromkeys(
                (
                    "tool_synthetic_simulation_passed"
                    if status is ToolVerificationStatus.SIMULATION_PASSED
                    else "tool_synthetic_simulation_failed",
                    "tool_output_canonicalized",
                    "tool_artifact_fingerprinted",
                    *effect_reason_codes,
                )
            )
        )
        payload = {
            "schema_version": "aion-knowledge-tool-simulation/v1",
            "simulation_id": f"simulation-{plan.plan_id}",
            "plan_id": plan.plan_id,
            "status": status,
            "artifacts": (artifact,),
            "observed_effects": step.expected_effects,
            "expected_effects_satisfied": expected_satisfied,
            "forbidden_effects_absent": forbidden_absent,
            "reason_codes": reason_codes,
            "canonical_output": canonical_output,
            "output_fingerprint": output_fingerprint,
            "actual_tool_executed": False,
            "persistent_write_applied": False,
            "runtime_effect": False,
        }
        return ToolSimulationResult.model_validate(
            {**payload, "simulation_fingerprint": tool_simulation_fingerprint(payload)}
        )


__all__ = [
    "ExplicitLocalToolVerificationFixtureReplay",
    "SyntheticToolSimulator",
    "assert_tool_fixture_path_allowed",
    "build_tool_fixture_envelope",
]
