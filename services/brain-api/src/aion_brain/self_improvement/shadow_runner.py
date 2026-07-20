"""Explicit Python runner for controlled shadow-mode execution."""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

from aion_brain.contracts.self_improvement_shadow import (
    canonical_shadow_fingerprint,
    require_safe_identifier,
)
from aion_brain.production_auth.canonical import canonical_json_text
from aion_brain.self_improvement.shadow_budget import (
    ShadowResourceBudget,
    ShadowResourceUsage,
    evaluate_shadow_budget,
)
from aion_brain.self_improvement.shadow_evidence import (
    ShadowEvidenceBundle,
    ShadowRunDiagnostics,
    ShadowRunResult,
)
from aion_brain.self_improvement.shadow_mode import EphemeralShadowStore
from aion_brain.self_improvement.shadow_observation import (
    InMemoryShadowReferenceAdapter,
    ShadowReferenceSnapshot,
)
from aion_brain.self_improvement.shadow_pipeline import ControlledShadowPipeline, ShadowIdFactory


class ControlledShadowModeRunner:
    """Run an injected shadow pipeline and optionally write one evidence file."""

    def __init__(
        self,
        *,
        pipeline: ControlledShadowPipeline,
        ephemeral_store: EphemeralShadowStore | None = None,
        repository_root: Path | None = None,
    ) -> None:
        self._pipeline = pipeline
        self._store = ephemeral_store
        self._repository_root = repository_root.resolve(strict=True) if repository_root else None

    def run(
        self,
        manifest: object,
        *,
        output_directory: Path | None = None,
    ) -> ShadowRunResult:
        """Run the shadow pipeline, writing no files unless explicitly requested."""

        bundle = self._pipeline.run(manifest)  # type: ignore[arg-type]
        if self._store is not None:
            self._store.put(bundle)
        if output_directory is None:
            return ShadowRunResult(
                bundle=bundle,
                output_bytes=0,
                written=False,
                reason_codes=("shadow_output_boundary_satisfied",),
            )
        output_path = self._validate_output_directory(output_directory)
        file_name = f"{bundle.run_id}.json"
        require_safe_identifier(bundle.run_id, "run_id")
        target = output_path / file_name
        if target.exists():
            raise RuntimeError("shadow_output_boundary_rejected")
        text = canonical_json_text(bundle.model_dump(mode="python"))
        encoded = text.encode("utf-8")
        projected_usage = ShadowResourceUsage(output_bytes=len(encoded), output_files=1)
        if len(encoded) > bundle.resource_budget.maximum_output_bytes:
            raise RuntimeError("shadow_output_boundary_rejected")
        if projected_usage.output_files > bundle.resource_budget.maximum_operator_output_files:
            raise RuntimeError("shadow_output_boundary_rejected")
        with target.open("x", encoding="utf-8") as handle:
            handle.write(text)
        written_bundle = _bundle_with_output_usage(
            bundle,
            output_bytes=len(encoded),
            output_files=1,
        )
        return ShadowRunResult(
            bundle=written_bundle,
            output_files=(file_name,),
            output_bytes=len(encoded),
            written=True,
            reason_codes=("shadow_output_boundary_satisfied",),
        )

    def _validate_output_directory(self, output_directory: Path) -> Path:
        text = str(output_directory)
        if "://" in text or text.startswith("//"):
            raise RuntimeError("shadow_output_boundary_rejected")
        if not output_directory.is_absolute():
            raise RuntimeError("shadow_output_boundary_rejected")
        resolved = output_directory.resolve(strict=True)
        if not resolved.is_dir():
            raise RuntimeError("shadow_output_boundary_rejected")
        if any(part.startswith(".") for part in resolved.parts if part not in {"/"}):
            raise RuntimeError("shadow_output_boundary_rejected")
        if self._repository_root is not None:
            root = self._repository_root
            if resolved == root or root in resolved.parents:
                raise RuntimeError("shadow_output_boundary_rejected")
        return resolved


def replay_shadow_run(
    *,
    manifest: object,
    resolved_snapshots: Iterable[ShadowReferenceSnapshot],
    resource_budget: ShadowResourceBudget,
    fixed_clock: object,
    fixed_id_factory: ShadowIdFactory,
) -> ShadowEvidenceBundle:
    """Replay a shadow run deterministically from supplied snapshots."""

    if not callable(fixed_clock):
        raise ValueError("fixed clock must be callable")
    adapter = InMemoryShadowReferenceAdapter(tuple(resolved_snapshots))
    pipeline = ControlledShadowPipeline(
        reference_adapter=adapter,
        resource_budget=resource_budget,
        clock=fixed_clock,
        monotonic_clock=lambda: 0.0,
        id_factory=fixed_id_factory,
    )
    return pipeline.run(manifest)  # type: ignore[arg-type]


def shadow_bundle_fingerprint(bundle: ShadowEvidenceBundle) -> str:
    """Return the canonical evidence bundle fingerprint."""

    return canonical_shadow_fingerprint(bundle.model_dump(mode="python"))


def _bundle_with_output_usage(
    bundle: ShadowEvidenceBundle,
    *,
    output_bytes: int,
    output_files: int,
) -> ShadowEvidenceBundle:
    usage = bundle.resource_usage.model_copy(
        update={"output_bytes": output_bytes, "output_files": output_files}
    )
    diagnostic_payload = bundle.diagnostics.model_dump(mode="python")
    diagnostic_payload.pop("fingerprint", None)
    diagnostic_payload["output_bytes"] = output_bytes
    diagnostic_payload["output_files"] = output_files
    diagnostics = ShadowRunDiagnostics(**diagnostic_payload)
    payload = bundle.model_dump(mode="python")
    payload.pop("fingerprint", None)
    payload["resource_usage"] = usage
    payload["budget_decision"] = evaluate_shadow_budget(usage, bundle.resource_budget)
    payload["diagnostics"] = diagnostics
    return ShadowEvidenceBundle(**payload)


__all__ = [
    "ControlledShadowModeRunner",
    "replay_shadow_run",
    "shadow_bundle_fingerprint",
]
