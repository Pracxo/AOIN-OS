"""Deterministic expected-vs-observed effect verification."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from aion_brain.contracts.effects import ExpectedEffect, ObservedEffect
from aion_brain.contracts.outcomes import (
    EffectVerificationRequest,
    EffectVerificationRun,
    VerificationStatus,
)
from aion_brain.outcomes._shared import (
    audit_optional,
    authorize,
    clamp_score,
    emit_telemetry,
    provenance_optional,
)
from aion_brain.outcomes.repository import OutcomeRepository


class EffectVerifier:
    """Compare expected effects with observed effects without model judgement."""

    def __init__(
        self,
        repository: OutcomeRepository,
        policy_adapter: object,
        *,
        observed_effect_collector: object | None = None,
        telemetry_service: object | None = None,
        audit_sink: object | None = None,
        provenance_service: object | None = None,
        settings: object | None = None,
    ) -> None:
        self._repository = repository
        self._policy_adapter = policy_adapter
        self._collector = observed_effect_collector
        self._telemetry_service = telemetry_service
        self._audit_sink = audit_sink
        self._provenance_service = provenance_service
        self._settings = settings

    def verify(self, request: EffectVerificationRequest) -> EffectVerificationRun:
        """Run deterministic verification and optionally update only the OutcomeRecord."""
        try:
            authorize(
                self._policy_adapter,
                action_type="outcome.verify",
                resource_type="outcome_verification",
                resource_id=request.verification_run_id,
                scope=request.owner_scope,
                trace_id=request.trace_id,
                risk_level="medium" if request.mode == "controlled" else "low",
                context={"mode": request.mode},
            )
        except PermissionError:
            return self._blocked_run(request)

        run_id = request.verification_run_id or f"effect-verification-{uuid4().hex}"
        emit_telemetry(
            self._telemetry_service,
            event_type="effect_verification_started",
            node_type="effect_verification",
            node_id=run_id,
            intensity=0.4,
            trace_id=request.trace_id,
            payload={"owner_scope": request.owner_scope, "mode": request.mode},
        )
        expected = self._load_expected(request)
        observed = self._load_observed(request)
        if request.collect_observed_effects and request.source_type and request.source_id:
            collect = getattr(self._collector, "collect_for_source", None)
            if callable(collect):
                try:
                    collected = collect(
                        request.source_type,
                        request.source_id,
                        request.owner_scope,
                        request.trace_id,
                    )
                    if isinstance(collected, list):
                        observed.extend(
                            item for item in collected if isinstance(item, ObservedEffect)
                        )
                except Exception:
                    pass
        comparison = compare_effects(expected, observed)
        score = score_comparison(expected, comparison)
        status = verification_status(comparison, request.mode)
        now = datetime.now(UTC)
        run = EffectVerificationRun(
            verification_run_id=run_id,
            trace_id=request.trace_id,
            outcome_id=request.outcome_id,
            source_type=request.source_type,
            source_id=request.source_id,
            status=status,
            mode=request.mode,
            owner_scope=request.owner_scope,
            expected_effect_ids=[item.expected_effect_id for item in expected],
            observed_effect_ids=[item.observed_effect_id for item in observed],
            matched_effects=comparison["matched_effects"],
            missing_effects=comparison["missing_effects"],
            unexpected_effects=comparison["unexpected_effects"],
            contradicted_effects=comparison["contradicted_effects"],
            score=score,
            result={
                "deterministic": True,
                "mutated_source_records": False,
                "updated_outcome_record": request.mode == "controlled" and bool(request.outcome_id),
            },
            created_by=request.created_by,
            created_at=now,
            completed_at=now,
        )
        stored = self._repository.save_verification_run(run)
        if request.mode == "controlled" and request.outcome_id:
            outcome = self._repository.get_outcome(request.outcome_id)
            if outcome is not None:
                updated = outcome.model_copy(
                    update={
                        "status": _outcome_status_from_verification(stored),
                        "score": stored.score,
                        "updated_at": now,
                        "metadata": {
                            **outcome.metadata,
                            "verification_run_id": stored.verification_run_id,
                        },
                    }
                )
                self._repository.save_outcome(updated)
        audit_optional(
            self._audit_sink,
            "effect_verification_completed",
            {"verification_run_id": stored.verification_run_id, "score": stored.score},
        )
        for effect_id in stored.expected_effect_ids:
            provenance_optional(
                self._provenance_service,
                stored.verification_run_id,
                effect_id,
                "verifies_expected_effect",
            )
        for effect_id in stored.observed_effect_ids:
            provenance_optional(
                self._provenance_service,
                stored.verification_run_id,
                effect_id,
                "uses_observed_effect",
            )
        emit_telemetry(
            self._telemetry_service,
            event_type="effect_verification_completed",
            node_type="effect_verification",
            node_id=stored.verification_run_id,
            intensity=stored.score,
            trace_id=stored.trace_id,
            payload={"owner_scope": stored.owner_scope, "status": stored.status},
        )
        return stored

    def get(self, verification_run_id: str) -> EffectVerificationRun | None:
        """Return one verification run."""
        return self._repository.get_verification_run(verification_run_id)

    def list_verification_runs(
        self,
        status: str | None = None,
        limit: int = 100,
    ) -> list[EffectVerificationRun]:
        """List verification runs for operator summaries."""
        return self._repository.list_verification_runs(status=status, limit=limit)

    def _load_expected(self, request: EffectVerificationRequest) -> list[ExpectedEffect]:
        if request.expected_effect_ids:
            return [
                effect
                for effect_id in request.expected_effect_ids
                if (effect := self._repository.get_expected_effect(effect_id)) is not None
            ]
        if request.outcome_id and (outcome := self._repository.get_outcome(request.outcome_id)):
            return [
                effect
                for effect_id in outcome.expected_effects
                if (effect := self._repository.get_expected_effect(effect_id)) is not None
            ]
        return self._repository.list_expected_effects(
            source_type=request.source_type,
            source_id=request.source_id,
            trace_id=request.trace_id,
            limit=500,
        )

    def _load_observed(self, request: EffectVerificationRequest) -> list[ObservedEffect]:
        if request.observed_effect_ids:
            return [
                effect
                for effect_id in request.observed_effect_ids
                if (effect := self._repository.get_observed_effect(effect_id)) is not None
            ]
        if request.outcome_id and (outcome := self._repository.get_outcome(request.outcome_id)):
            return [
                effect
                for effect_id in outcome.observed_effects
                if (effect := self._repository.get_observed_effect(effect_id)) is not None
            ]
        return self._repository.list_observed_effects(
            source_type=request.source_type,
            source_id=request.source_id,
            trace_id=request.trace_id,
            limit=500,
        )

    def _blocked_run(self, request: EffectVerificationRequest) -> EffectVerificationRun:
        now = datetime.now(UTC)
        run = EffectVerificationRun(
            verification_run_id=request.verification_run_id or f"effect-verification-{uuid4().hex}",
            trace_id=request.trace_id,
            outcome_id=request.outcome_id,
            source_type=request.source_type,
            source_id=request.source_id,
            status="blocked_by_policy",
            mode=request.mode,
            owner_scope=request.owner_scope,
            score=0.0,
            result={"blocked": "policy_denied", "mutated_source_records": False},
            created_by=request.created_by,
            created_at=now,
            completed_at=now,
        )
        emit_telemetry(
            self._telemetry_service,
            event_type="effect_verification_failed",
            node_type="effect_verification",
            node_id=run.verification_run_id,
            intensity=1.0,
            trace_id=run.trace_id,
            payload={"owner_scope": run.owner_scope, "status": run.status},
        )
        return self._repository.save_verification_run(run)


def compare_effects(
    expected: list[ExpectedEffect],
    observed: list[ObservedEffect],
) -> dict[str, list[dict[str, Any]]]:
    """Compare effects and return public result buckets."""
    matched: list[dict[str, Any]] = []
    missing: list[dict[str, Any]] = []
    contradicted: list[dict[str, Any]] = []
    matched_observed: set[str] = set()
    for effect in expected:
        candidates = [item for item in observed if _same_effect_identity(effect, item)]
        passing = [item for item in candidates if satisfies_success_criteria(effect, item)]
        if passing:
            first = passing[0]
            matched_observed.add(first.observed_effect_id)
            matched.append(
                {
                    "expected_effect_id": effect.expected_effect_id,
                    "observed_effect_id": first.observed_effect_id,
                    "required": effect.required,
                    "confidence": min(effect.confidence, first.confidence),
                }
            )
            continue
        if candidates:
            contradicted.extend(
                {
                    "expected_effect_id": effect.expected_effect_id,
                    "observed_effect_id": candidate.observed_effect_id,
                    "required": effect.required,
                    "reason": "success_criteria_not_satisfied",
                }
                for candidate in candidates
            )
        missing.append(
            {
                "expected_effect_id": effect.expected_effect_id,
                "required": effect.required,
                "predicate": effect.predicate,
                "effect_type": effect.effect_type,
            }
        )
    unexpected = [
        {
            "observed_effect_id": item.observed_effect_id,
            "predicate": item.predicate,
            "effect_type": item.effect_type,
        }
        for item in observed
        if item.observed_effect_id not in matched_observed
        and not any(_same_effect_identity(effect, item) for effect in expected)
    ]
    return {
        "matched_effects": matched,
        "missing_effects": missing,
        "unexpected_effects": unexpected,
        "contradicted_effects": contradicted,
    }


def satisfies_success_criteria(expected: ExpectedEffect, observed: ObservedEffect) -> bool:
    """Evaluate supported success criteria without dynamic code."""
    criteria = expected.success_criteria or {"equals": expected.expected_value}
    observed_value = observed.observed_value
    for key, expected_value in criteria.items():
        if key == "equals" and observed_value != expected_value:
            return False
        if key == "not_equals" and observed_value == expected_value:
            return False
        if key == "exists" and bool(expected_value) and observed_value in ({}, [], None):
            return False
        if key == "contains" and not _contains(observed_value, expected_value):
            return False
        if key == "gte" and not _compare_number(observed_value, expected_value, ">="):
            return False
        if key == "lte" and not _compare_number(observed_value, expected_value, "<="):
            return False
        if key == "status_is" and str(observed_value.get("status")) != str(expected_value):
            return False
        if key == "truthy" and bool(expected_value) and not bool(observed_value):
            return False
    return True


def score_comparison(
    expected: list[ExpectedEffect],
    comparison: dict[str, list[dict[str, Any]]],
) -> float:
    """Score matches, optional matches, contradiction penalty, and confidence."""
    required_total = len([item for item in expected if item.required])
    optional_total = len(expected) - required_total
    required_matched = len(
        [item for item in comparison["matched_effects"] if bool(item.get("required"))]
    )
    optional_matched = len(
        [item for item in comparison["matched_effects"] if not bool(item.get("required"))]
    )
    required_score = 1.0 if required_total == 0 else required_matched / required_total
    optional_score = 1.0 if optional_total == 0 else optional_matched / optional_total
    contradiction_penalty = min(0.4, 0.1 * len(comparison["contradicted_effects"]))
    confidences = [float(item.get("confidence", 0.5)) for item in comparison["matched_effects"]]
    confidence_score = sum(confidences) / len(confidences) if confidences else 0.0
    return clamp_score(
        (required_score * 0.7)
        + (optional_score * 0.2)
        + (confidence_score * 0.1)
        - contradiction_penalty
    )


def verification_status(
    comparison: dict[str, list[dict[str, Any]]],
    mode: str,
) -> VerificationStatus:
    """Return verification status for comparison buckets."""
    if comparison["contradicted_effects"]:
        return "failed"
    required_missing = [
        item for item in comparison["missing_effects"] if bool(item.get("required"))
    ]
    if required_missing:
        return "failed"
    if comparison["missing_effects"] or comparison["unexpected_effects"]:
        return "partial"
    if mode == "dry_run":
        return "dry_run"
    return "passed"


def _same_effect_identity(expected: ExpectedEffect, observed: ObservedEffect) -> bool:
    if expected.effect_type != observed.effect_type:
        return False
    if expected.predicate != observed.predicate:
        return False
    if expected.subject_ref and expected.subject_ref != observed.subject_ref:
        return False
    if expected.object_ref and expected.object_ref != observed.object_ref:
        return False
    return True


def _contains(observed_value: dict[str, Any], expected_value: object) -> bool:
    if isinstance(expected_value, dict):
        return all(observed_value.get(key) == value for key, value in expected_value.items())
    if isinstance(expected_value, list):
        return all(item in observed_value.values() for item in expected_value)
    return expected_value in observed_value.values()


def _compare_number(observed_value: dict[str, Any], expected_value: object, op: str) -> bool:
    observed_number = _number_from(observed_value)
    expected_number = _number_from(expected_value)
    if observed_number is None or expected_number is None:
        return False
    if op == ">=":
        return observed_number >= expected_number
    return observed_number <= expected_number


def _number_from(value: object) -> float | None:
    if isinstance(value, int | float):
        return float(value)
    if isinstance(value, dict):
        candidate = value.get("value")
        if isinstance(candidate, int | float):
            return float(candidate)
    return None


def _outcome_status_from_verification(run: EffectVerificationRun) -> str:
    if run.contradicted_effects:
        return "contradicted"
    if run.status in {"passed", "dry_run"} and run.score >= 0.75:
        return "verified"
    if run.status == "partial":
        return "partial"
    if run.status == "failed":
        return "failed"
    return "unknown"


__all__ = [
    "EffectVerifier",
    "compare_effects",
    "satisfies_success_criteria",
    "score_comparison",
    "verification_status",
]
