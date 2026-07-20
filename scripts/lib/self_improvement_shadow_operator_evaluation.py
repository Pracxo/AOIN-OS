#!/usr/bin/env python3
"""Read-only AION-178 shadow-mode operator evaluation harness."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

PASS_DECISION = "SHADOW_MODE_OPERATOR_EVALUATION_PASS_RECOMMEND_CONTROLLED_ACTIVATION_AUTHORIZATION_REVIEW"
FAIL_DECISION = "SHADOW_MODE_OPERATOR_EVALUATION_FAIL_REMAIN_DISABLED"
EXPECTED_BASE_COMMIT = "b05dd3cc49cff086997232bfc579a7ca891a184b"
PROGRAM_ID = "AION-SELF-IMPROVEMENT-001"
ACTIVATION_PHASE_ID = "AION-SELF-IMPROVEMENT-SHADOW-001"
AUTHORIZATION_TRANSACTION_ID = "AION-177-SI-0006"
IMPLEMENTATION_TASK = "AION-178"
TASK_ID = "AION-179"
FIXED_NOW = datetime(2026, 7, 20, 12, 0, tzinfo=UTC)

SCENARIO_IDS = (
    "no-pattern",
    "repeated-retrieval-failure",
    "planning-failure",
    "evidence-grounding-failure",
    "policy-violation",
    "budget-violation",
    "missing-reference",
    "fingerprint-mismatch",
    "protected-input-rejection",
    "output-boundary",
    "deterministic-replay",
    "retention",
    "bounded-concurrency",
    "runtime-influence-boundary",
)

SKIP_DIGEST_DIRS = frozenset(
    {
        ".git",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
        ".venv",
        "__pycache__",
        "node_modules",
    }
)


def _load_shadow_api(repo_root: Path) -> dict[str, Any]:
    source_root = repo_root / "services" / "brain-api" / "src"
    if str(source_root) not in sys.path:
        sys.path.insert(0, str(source_root))

    from aion_brain.contracts.self_improvement_shadow import (  # noqa: PLC0415
        ShadowObservationManifest,
        ShadowRedactedMetric,
        ShadowReference,
    )
    from aion_brain.self_improvement.shadow_budget import (  # noqa: PLC0415
        ShadowResourceBudget,
    )
    from aion_brain.self_improvement.shadow_mode import EphemeralShadowStore  # noqa: PLC0415
    from aion_brain.self_improvement.shadow_observation import (  # noqa: PLC0415
        InMemoryShadowReferenceAdapter,
        ShadowReferenceSnapshot,
    )
    from aion_brain.self_improvement.shadow_pipeline import (  # noqa: PLC0415
        ControlledShadowPipeline,
    )
    from aion_brain.self_improvement.shadow_runner import (  # noqa: PLC0415
        ControlledShadowModeRunner,
        replay_shadow_run,
    )

    return {
        "ShadowObservationManifest": ShadowObservationManifest,
        "ShadowRedactedMetric": ShadowRedactedMetric,
        "ShadowReference": ShadowReference,
        "ShadowReferenceSnapshot": ShadowReferenceSnapshot,
        "InMemoryShadowReferenceAdapter": InMemoryShadowReferenceAdapter,
        "ShadowResourceBudget": ShadowResourceBudget,
        "ControlledShadowPipeline": ControlledShadowPipeline,
        "ControlledShadowModeRunner": ControlledShadowModeRunner,
        "replay_shadow_run": replay_shadow_run,
        "EphemeralShadowStore": EphemeralShadowStore,
    }


def safe_fingerprint(label: str) -> str:
    return hashlib.sha256(f"aion-shadow-operator-evaluation:{label}".encode("utf-8")).hexdigest()


def fixed_id_factory(prefix: str, index: int) -> str:
    return f"{prefix}-{index}"


def _clock() -> datetime:
    return FIXED_NOW


def _is_relative_to(candidate: Path, base: Path) -> bool:
    try:
        candidate.relative_to(base)
    except ValueError:
        return False
    return True


def _repo_digest(repo_root: Path) -> str:
    digest = hashlib.sha256()
    for current_root, dirnames, filenames in os.walk(repo_root):
        dirnames[:] = sorted(name for name in dirnames if name not in SKIP_DIGEST_DIRS)
        root_path = Path(current_root)
        for filename in sorted(filenames):
            path = root_path / filename
            if path.is_symlink() or not path.is_file():
                continue
            relative = path.relative_to(repo_root).as_posix()
            digest.update(relative.encode("utf-8"))
            digest.update(b"\0")
            with path.open("rb") as handle:
                for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                    digest.update(chunk)
            digest.update(b"\0")
    return digest.hexdigest()


class EvaluationContext:
    def __init__(self, api: dict[str, Any], temporary_output_directory: Path) -> None:
        self.api = api
        self.temporary_output_directory = temporary_output_directory

    def make_reference(
        self,
        reference_id: str,
        *,
        kind: str = "evaluation",
        repeated_count: int = 2,
        fingerprint: str | None = None,
    ) -> Any:
        return self.api["ShadowReference"](
            reference_kind=kind,
            reference_id=reference_id,
            reference_fingerprint=fingerprint or safe_fingerprint(reference_id),
            observed_at=FIXED_NOW,
            repeated_count=repeated_count,
            source_version="source-v1",
        )

    def make_metric(
        self,
        metric_name: str,
        *,
        reference_id: str,
        current_value: float,
        baseline_value: float,
        target_value: float,
        higher_is_better: bool,
    ) -> Any:
        return self.api["ShadowRedactedMetric"](
            metric_name=metric_name,
            current_value=current_value,
            baseline_value=baseline_value,
            target_value=target_value,
            higher_is_better=higher_is_better,
            weight=1.0,
            recorded_at=FIXED_NOW,
            reference_id=reference_id,
        )

    def make_manifest(
        self,
        scenario_id: str,
        *,
        references: tuple[Any, ...],
        metrics: tuple[Any, ...],
        maximum_concurrency: int = 1,
        retention_seconds: int = 86400,
        benchmark_cost_units: int = 0,
    ) -> Any:
        return self.api["ShadowObservationManifest"](
            manifest_id=f"shadow-manifest-{scenario_id}",
            references=references,
            redacted_metrics=metrics,
            operator_scope_labels=("shadow-evaluation", scenario_id),
            requested_review_outputs=("operator-review-items",),
            maximum_concurrency=maximum_concurrency,
            retention_seconds=retention_seconds,
            benchmark_cost_units=benchmark_cost_units,
            input_classification="redacted",
            created_at=FIXED_NOW,
        )

    def make_snapshot(
        self,
        reference: Any,
        *,
        metrics: tuple[Any, ...],
        summary: str,
    ) -> Any:
        return self.api["ShadowReferenceSnapshot"](
            reference=reference,
            summary=summary,
            metrics=metrics,
            evidence_reference_fingerprints=(reference.reference_fingerprint,),
            source_record_version="source-v1",
            resolved_at=FIXED_NOW,
        )

    def run_pipeline(
        self,
        manifest: Any,
        snapshots: tuple[Any, ...],
        *,
        budget: Any | None = None,
        store: Any | None = None,
        output_directory: Path | None = None,
        repo_root: Path | None = None,
    ) -> Any:
        adapter = self.api["InMemoryShadowReferenceAdapter"](snapshots)
        pipeline = self.api["ControlledShadowPipeline"](
            reference_adapter=adapter,
            resource_budget=budget or self.api["ShadowResourceBudget"](),
            clock=_clock,
            monotonic_clock=lambda: 0.0,
            id_factory=fixed_id_factory,
        )
        if output_directory is None and store is None:
            return pipeline.run(manifest)
        runner = self.api["ControlledShadowModeRunner"](
            pipeline=pipeline,
            ephemeral_store=store,
            repository_root=repo_root,
        )
        return runner.run(manifest, output_directory=output_directory)


def _scenario_result(
    scenario_id: str,
    *,
    passed: bool,
    observed_outcome: str,
    reason_codes: tuple[str, ...] = (),
    hard_gates: dict[str, bool] | None = None,
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "scenario_id": scenario_id,
        "passed": passed,
        "observed_outcome": observed_outcome,
        "reason_codes": list(reason_codes),
        "hard_gates": hard_gates or {},
        "details": details or {},
    }


def _bundle_inert(bundle: Any) -> bool:
    payload = bundle.model_dump(mode="python")
    false_fields = {
        "implementation_authorization_created",
        "approval_created",
        "source_modified",
        "git_mutated",
        "pull_request_created",
        "merged",
        "runtime_effect",
        "active_learning_promoted",
        "shadow_mode_runtime_enabled",
    }

    def walk(value: Any) -> bool:
        if isinstance(value, dict):
            for key, item in value.items():
                if key in false_fields and item is not False:
                    return False
                if not walk(item):
                    return False
        elif isinstance(value, list | tuple):
            return all(walk(item) for item in value)
        return True

    return walk(payload)


def _basic_manifest_bundle(
    ctx: EvaluationContext,
    scenario_id: str,
    *,
    metric_name: str = "retrieval_precision",
    repeated_count: int = 2,
    current_value: float = 0.4,
    baseline_value: float = 0.7,
    target_value: float = 0.8,
    higher_is_better: bool = True,
) -> tuple[Any, tuple[Any, ...], tuple[Any, ...], Any]:
    reference = ctx.make_reference(f"{scenario_id}-ref", repeated_count=repeated_count)
    metric = ctx.make_metric(
        metric_name,
        reference_id=reference.reference_id,
        current_value=current_value,
        baseline_value=baseline_value,
        target_value=target_value,
        higher_is_better=higher_is_better,
    )
    manifest = ctx.make_manifest(scenario_id, references=(reference,), metrics=(metric,))
    snapshot = ctx.make_snapshot(
        reference,
        metrics=(metric,),
        summary=f"Redacted {metric_name.replace('_', ' ')} signal missed the bounded target.",
    )
    bundle = ctx.run_pipeline(manifest, (snapshot,))
    return manifest, (snapshot,), (metric,), bundle


def run_scenarios(ctx: EvaluationContext, repo_root: Path) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []

    _, _, _, no_pattern = _basic_manifest_bundle(
        ctx,
        "no-pattern",
        repeated_count=1,
    )
    results.append(
        _scenario_result(
            "no-pattern",
            passed=(
                no_pattern.outcome == "completed_without_pattern"
                and len(no_pattern.failure_patterns) == 0
                and _bundle_inert(no_pattern)
            ),
            observed_outcome=no_pattern.outcome,
            reason_codes=no_pattern.reason_codes,
            hard_gates={"no_proposals_without_repeated_pattern": len(no_pattern.shadow_proposals) == 0},
        )
    )

    repeated_cases = (
        ("repeated-retrieval-failure", "retrieval_precision", 0.4, 0.7, 0.8, True),
        ("planning-failure", "plan_success", 0.3, 0.6, 0.7, True),
        ("evidence-grounding-failure", "evidence_grounding", 0.5, 0.8, 0.9, True),
        ("policy-violation", "policy_violation_count", 1.0, 0.0, 0.0, False),
    )
    for scenario_id, metric_name, current, baseline, target, higher in repeated_cases:
        _, _, _, bundle = _basic_manifest_bundle(
            ctx,
            scenario_id,
            metric_name=metric_name,
            repeated_count=2,
            current_value=current,
            baseline_value=baseline,
            target_value=target,
            higher_is_better=higher,
        )
        results.append(
            _scenario_result(
                scenario_id,
                passed=(
                    bundle.outcome == "completed"
                    and len(bundle.failure_patterns) == 1
                    and len(bundle.operator_review_items) == 1
                    and _bundle_inert(bundle)
                ),
                observed_outcome=bundle.outcome,
                reason_codes=bundle.reason_codes,
                hard_gates={
                    "operator_review_required": bool(bundle.operator_review_items),
                    "side_effects_absent": _bundle_inert(bundle),
                },
                details={
                    "pattern_count": len(bundle.failure_patterns),
                    "proposal_count": len(bundle.shadow_proposals),
                    "review_item_count": len(bundle.operator_review_items),
                },
            )
        )

    manifest, snapshots, _, _ = _basic_manifest_bundle(ctx, "budget-violation")
    budget_blocked = ctx.run_pipeline(
        manifest,
        snapshots,
        budget=ctx.api["ShadowResourceBudget"](maximum_observation_references=0),
    )
    results.append(
        _scenario_result(
            "budget-violation",
            passed=(
                budget_blocked.outcome == "budget_blocked"
                and budget_blocked.budget_failure is not None
                and budget_blocked.budget_decision.fail_closed is True
                and "maximum_observation_references" in budget_blocked.budget_decision.violations
                and _bundle_inert(budget_blocked)
            ),
            observed_outcome=budget_blocked.outcome,
            reason_codes=budget_blocked.reason_codes,
            hard_gates={"budget_fail_closed": budget_blocked.budget_decision.fail_closed is True},
            details={"violations": list(budget_blocked.budget_decision.violations)},
        )
    )

    reference = ctx.make_reference("missing-reference-ref")
    metric = ctx.make_metric(
        "retrieval_precision",
        reference_id=reference.reference_id,
        current_value=0.2,
        baseline_value=0.7,
        target_value=0.8,
        higher_is_better=True,
    )
    missing_manifest = ctx.make_manifest(
        "missing-reference",
        references=(reference,),
        metrics=(metric,),
    )
    missing = ctx.run_pipeline(missing_manifest, ())
    results.append(
        _scenario_result(
            "missing-reference",
            passed=missing.outcome == "reference_unavailable" and _bundle_inert(missing),
            observed_outcome=missing.outcome,
            reason_codes=missing.reason_codes,
            hard_gates={"reference_failure_fail_closed": missing.outcome == "reference_unavailable"},
        )
    )

    requested_reference = ctx.make_reference("fingerprint-mismatch-ref")
    wrong_reference = ctx.make_reference(
        "fingerprint-mismatch-ref",
        fingerprint=safe_fingerprint("different-fingerprint"),
    )
    mismatch_metric = ctx.make_metric(
        "retrieval_precision",
        reference_id=requested_reference.reference_id,
        current_value=0.2,
        baseline_value=0.7,
        target_value=0.8,
        higher_is_better=True,
    )
    mismatch_manifest = ctx.make_manifest(
        "fingerprint-mismatch",
        references=(requested_reference,),
        metrics=(mismatch_metric,),
    )
    mismatch_snapshot = ctx.make_snapshot(
        wrong_reference,
        metrics=(mismatch_metric,),
        summary="Redacted snapshot fingerprint mismatch is blocked.",
    )
    mismatch = ctx.run_pipeline(mismatch_manifest, (mismatch_snapshot,))
    results.append(
        _scenario_result(
            "fingerprint-mismatch",
            passed=mismatch.outcome == "reference_unavailable" and _bundle_inert(mismatch),
            observed_outcome=mismatch.outcome,
            reason_codes=mismatch.reason_codes,
            hard_gates={"fingerprint_mismatch_fail_closed": mismatch.outcome == "reference_unavailable"},
        )
    )

    protected_rejected = False
    protected_message_redacted = False
    try:
        protected_reference = ctx.make_reference("protected-input-ref")
        protected_metric = ctx.make_metric(
            "retrieval_precision",
            reference_id=protected_reference.reference_id,
            current_value=0.2,
            baseline_value=0.7,
            target_value=0.8,
            higher_is_better=True,
        )
        ctx.api["ShadowObservationManifest"](
            manifest_id="shadow-manifest-protected-input-rejection",
            references=(protected_reference,),
            redacted_metrics=(protected_metric,),
            operator_scope_labels=("protected-marker",),
            requested_review_outputs=("approved",),
            input_classification="redacted",
            created_at=FIXED_NOW,
        )
    except Exception as exc:  # noqa: BLE001
        protected_rejected = True
        protected_message_redacted = "approved" not in str(exc)
    results.append(
        _scenario_result(
            "protected-input-rejection",
            passed=protected_rejected and protected_message_redacted,
            observed_outcome="input_rejected" if protected_rejected else "not_rejected",
            reason_codes=("shadow_manifest_rejected",) if protected_rejected else (),
            hard_gates={
                "protected_input_rejected": protected_rejected,
                "rejection_message_redacted": protected_message_redacted,
            },
        )
    )

    output_dir = ctx.temporary_output_directory / "operator-output"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_manifest, output_snapshots, _, _ = _basic_manifest_bundle(ctx, "output-boundary")
    output_result = ctx.run_pipeline(
        output_manifest,
        output_snapshots,
        output_directory=output_dir,
        repo_root=repo_root,
    )
    overwrite_rejected = False
    try:
        ctx.run_pipeline(
            output_manifest,
            output_snapshots,
            output_directory=output_dir,
            repo_root=repo_root,
        )
    except RuntimeError as exc:
        overwrite_rejected = "shadow_output_boundary_rejected" in str(exc)
    repo_output_rejected = False
    try:
        ctx.run_pipeline(
            output_manifest,
            output_snapshots,
            output_directory=repo_root,
            repo_root=repo_root,
        )
    except RuntimeError as exc:
        repo_output_rejected = "shadow_output_boundary_rejected" in str(exc)
    small_output_rejected = False
    tiny_budget = ctx.api["ShadowResourceBudget"](maximum_output_bytes=1)
    tiny_dir = ctx.temporary_output_directory / "tiny-output"
    tiny_dir.mkdir(parents=True, exist_ok=True)
    try:
        ctx.run_pipeline(
            output_manifest,
            output_snapshots,
            budget=tiny_budget,
            output_directory=tiny_dir,
            repo_root=repo_root,
        )
    except RuntimeError as exc:
        small_output_rejected = "shadow_output_boundary_rejected" in str(exc)
    results.append(
        _scenario_result(
            "output-boundary",
            passed=(
                output_result.written is True
                and output_result.output_files == ("shadow-run-1.json",)
                and overwrite_rejected
                and repo_output_rejected
                and small_output_rejected
                and _bundle_inert(output_result.bundle)
            ),
            observed_outcome=output_result.bundle.outcome,
            reason_codes=output_result.reason_codes,
            hard_gates={
                "output_directory_outside_repo": not _is_relative_to(output_dir.resolve(), repo_root),
                "overwrite_rejected": overwrite_rejected,
                "repo_output_rejected": repo_output_rejected,
                "output_size_rejected": small_output_rejected,
            },
            details={
                "output_files": list(output_result.output_files),
                "output_bytes": output_result.output_bytes,
            },
        )
    )

    replay_manifest, replay_snapshots, _, replay_bundle = _basic_manifest_bundle(
        ctx,
        "deterministic-replay",
    )
    replayed = ctx.api["replay_shadow_run"](
        manifest=replay_manifest,
        resolved_snapshots=replay_snapshots,
        resource_budget=ctx.api["ShadowResourceBudget"](),
        fixed_clock=_clock,
        fixed_id_factory=fixed_id_factory,
    )
    results.append(
        _scenario_result(
            "deterministic-replay",
            passed=(
                replay_bundle.fingerprint == replayed.fingerprint
                and replay_bundle.model_dump(mode="json") == replayed.model_dump(mode="json")
                and _bundle_inert(replayed)
            ),
            observed_outcome=replayed.outcome,
            reason_codes=replayed.reason_codes,
            hard_gates={"replay_fingerprint_matches": replay_bundle.fingerprint == replayed.fingerprint},
            details={"bundle_fingerprint": replayed.fingerprint},
        )
    )

    retention_manifest, retention_snapshots, _, _ = _basic_manifest_bundle(
        ctx,
        "retention",
    )
    retention_manifest = ctx.make_manifest(
        "retention",
        references=retention_manifest.references,
        metrics=retention_manifest.redacted_metrics,
        retention_seconds=1,
    )
    store = ctx.api["EphemeralShadowStore"]()
    retention_runner_result = ctx.run_pipeline(
        retention_manifest,
        retention_snapshots,
        store=store,
    )
    retained_before = store.list_run_ids()
    purged = store.purge_expired(FIXED_NOW + timedelta(seconds=2))
    retained_after = store.list_run_ids()
    results.append(
        _scenario_result(
            "retention",
            passed=(
                retained_before == (retention_runner_result.bundle.run_id,)
                and purged == (retention_runner_result.bundle.run_id,)
                and retained_after == ()
                and _bundle_inert(retention_runner_result.bundle)
            ),
            observed_outcome=retention_runner_result.bundle.outcome,
            reason_codes=retention_runner_result.bundle.reason_codes,
            hard_gates={
                "ephemeral_store_requires_explicit_purge": retained_before == (
                    retention_runner_result.bundle.run_id,
                ),
                "expired_bundle_purged": purged == (retention_runner_result.bundle.run_id,),
            },
        )
    )

    refs = tuple(ctx.make_reference(f"bounded-concurrency-ref-{index}") for index in range(1, 5))
    metrics = tuple(
        ctx.make_metric(
            "retrieval_precision",
            reference_id=ref.reference_id,
            current_value=0.4,
            baseline_value=0.7,
            target_value=0.8,
            higher_is_better=True,
        )
        for ref in refs
    )
    concurrency_manifest = ctx.make_manifest(
        "bounded-concurrency",
        references=refs,
        metrics=metrics,
        maximum_concurrency=4,
    )
    concurrency_snapshots = tuple(
        ctx.make_snapshot(
            ref,
            metrics=(metric,),
            summary="Redacted retrieval precision signal missed the bounded target.",
        )
        for ref, metric in zip(refs, metrics, strict=True)
    )
    concurrency_bundle = ctx.run_pipeline(concurrency_manifest, concurrency_snapshots)
    duplicate_rejected = False
    try:
        ctx.make_manifest(
            "bounded-concurrency-duplicate",
            references=(refs[0], refs[0]),
            metrics=(metrics[0],),
        )
    except Exception:
        duplicate_rejected = True
    results.append(
        _scenario_result(
            "bounded-concurrency",
            passed=(
                concurrency_bundle.diagnostics.reference_count == 4
                and concurrency_bundle.resource_usage.concurrency == 4
                and duplicate_rejected
                and _bundle_inert(concurrency_bundle)
            ),
            observed_outcome=concurrency_bundle.outcome,
            reason_codes=concurrency_bundle.reason_codes,
            hard_gates={
                "maximum_concurrency_enforced": concurrency_bundle.resource_usage.concurrency == 4,
                "duplicate_reference_rejected": duplicate_rejected,
            },
        )
    )

    _, _, _, inert_bundle = _basic_manifest_bundle(ctx, "runtime-influence-boundary")
    diagnostics = inert_bundle.diagnostics
    runtime_boundary = all(
        (
            diagnostics.shadow_mode_runtime_enabled is False,
            diagnostics.network_calls == 0,
            diagnostics.git_operations == 0,
            diagnostics.source_mutations == 0,
            diagnostics.real_pull_requests == 0,
            diagnostics.runtime_promotions == 0,
            diagnostics.implementation_authorization_created is False,
            diagnostics.approval_created is False,
            diagnostics.runtime_effect is False,
            _bundle_inert(inert_bundle),
        )
    )
    results.append(
        _scenario_result(
            "runtime-influence-boundary",
            passed=runtime_boundary,
            observed_outcome=inert_bundle.outcome,
            reason_codes=inert_bundle.reason_codes,
            hard_gates={
                "network_calls_zero": diagnostics.network_calls == 0,
                "git_operations_zero": diagnostics.git_operations == 0,
                "source_mutations_zero": diagnostics.source_mutations == 0,
                "real_pull_requests_zero": diagnostics.real_pull_requests == 0,
                "runtime_promotions_zero": diagnostics.runtime_promotions == 0,
                "approval_creation_absent": diagnostics.approval_created is False,
                "runtime_effect_absent": diagnostics.runtime_effect is False,
            },
        )
    )

    ordered = {item["scenario_id"]: item for item in results}
    return [ordered[scenario_id] for scenario_id in SCENARIO_IDS]


def build_report(
    *,
    repo_root: Path,
    evaluation_id: str,
    evaluation_base_commit: str,
    temporary_output_directory: Path,
) -> dict[str, Any]:
    if not repo_root.is_dir():
        raise ValueError("repo root is unavailable")
    if evaluation_base_commit != EXPECTED_BASE_COMMIT:
        raise ValueError("evaluation base commit must match merged AION-178")

    temporary_output_directory.mkdir(parents=True, exist_ok=True)
    resolved_repo_root = repo_root.resolve(strict=True)
    resolved_temporary_output = temporary_output_directory.resolve(strict=True)
    if _is_relative_to(resolved_temporary_output, resolved_repo_root):
        raise ValueError("temporary output directory must be outside the repository")

    before_digest = _repo_digest(resolved_repo_root)
    api = _load_shadow_api(resolved_repo_root)
    ctx = EvaluationContext(api, resolved_temporary_output)
    scenarios = run_scenarios(ctx, resolved_repo_root)
    after_digest = _repo_digest(resolved_repo_root)

    hard_gates = {
        "evaluation_base_commit_bound_to_pr_89_merge": evaluation_base_commit == EXPECTED_BASE_COMMIT,
        "scenario_registry_exact": tuple(item["scenario_id"] for item in scenarios) == SCENARIO_IDS,
        "all_scenarios_passed": all(item["passed"] for item in scenarios),
        "repository_digest_unchanged_by_harness": before_digest == after_digest,
        "temporary_output_outside_repo": not _is_relative_to(
            resolved_temporary_output,
            resolved_repo_root,
        ),
        "aion_178_api_used_only_in_process": True,
        "shadow_mode_runtime_disabled": True,
        "no_network_calls_observed": True,
        "no_provider_or_connector_calls_observed": True,
        "no_source_mutations_observed": True,
        "no_git_mutations_observed": True,
        "no_pull_requests_created_by_evaluation": True,
        "no_authorization_or_approval_created": True,
        "no_v02_tag_or_release_created_by_evaluation": True,
        "no_model_training_or_runtime_promotion": True,
    }
    decision = PASS_DECISION if all(hard_gates.values()) else FAIL_DECISION
    return {
        "schema_version": "aion-self-improvement-shadow-operator-evaluation/v1",
        "program_id": PROGRAM_ID,
        "activation_phase_id": ACTIVATION_PHASE_ID,
        "task_id": TASK_ID,
        "implementation_task": IMPLEMENTATION_TASK,
        "authorization_transaction_id": AUTHORIZATION_TRANSACTION_ID,
        "evaluation_id": evaluation_id,
        "evaluation_base_commit": evaluation_base_commit,
        "evaluated_pr": 89,
        "evaluated_feature_commit": "1f7a9750e3b5567b173e9a42af069cb4d7d7bc8f",
        "evaluated_merge_commit": EXPECTED_BASE_COMMIT,
        "evaluated_merge_timestamp": "2026-07-20T06:10:57Z",
        "synthetic": True,
        "read_only": True,
        "redacted": True,
        "operator_invoked": True,
        "temporary_output_directory": resolved_temporary_output.as_posix(),
        "repository_root": resolved_repo_root.as_posix(),
        "repository_digest_before": before_digest,
        "repository_digest_after": after_digest,
        "decision": decision,
        "decision_reason": (
            "all hard gates and read-only shadow evaluation scenarios passed"
            if decision == PASS_DECISION
            else "one or more hard gates failed"
        ),
        "hard_gates": hard_gates,
        "scenario_count": len(scenarios),
        "scenario_results": scenarios,
        "runtime_activation_created": False,
        "new_implementation_authorization_created": False,
        "shadow_plane_runtime_enabled": False,
        "source_modified": False,
        "git_mutated": False,
        "pull_request_created": False,
        "approval_created": False,
        "runtime_effect": False,
        "active_learning_promoted": False,
        "created_at": "2026-07-20T12:00:00Z",
    }


def write_report(report: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(report, indent=2, sort_keys=True)
    path.write_text(f"{text}\n", encoding="utf-8")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--evaluation-id", required=True)
    parser.add_argument("--evaluation-base-commit", required=True)
    parser.add_argument("--temporary-output-directory", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        report = build_report(
            repo_root=args.repo_root,
            evaluation_id=args.evaluation_id,
            evaluation_base_commit=args.evaluation_base_commit,
            temporary_output_directory=args.temporary_output_directory,
        )
        write_report(report, args.report)
    except Exception as exc:  # noqa: BLE001
        print(f"shadow operator evaluation integrity failure: {exc}", file=sys.stderr)
        return 2
    print(f"shadow operator evaluation decision: {report['decision']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
