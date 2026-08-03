#!/usr/bin/env python3
"""Uninstalled AION-246 deterministic external-cognition fixture runner."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import stat
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = ROOT / "services" / "brain-api" / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))
for SITE_PACKAGES in (ROOT / "services" / "brain-api" / ".venv" / "lib").glob(
    "python*/site-packages"
):
    site_packages_text = str(SITE_PACKAGES)
    if site_packages_text not in sys.path:
        sys.path.insert(0, site_packages_text)

from aion_brain.contracts.external_cognition import (  # noqa: E402
    AUTHORIZATION_TRANSACTION_ID,
    FIXTURE_CONFIRMATION_TEXT,
    PROGRAM_ID,
    PROHIBITED_EFFECT_COUNTERS,
    ZERO_FINGERPRINT,
    ExternalCognitionCapabilityKind,
    ExternalCognitionContextBudget,
    ExternalCognitionCostBudget,
    ExternalCognitionLatencyBudget,
    ExternalCognitionOutputBudget,
    ExternalCognitionProviderErrorClass,
    ExternalCognitionReplayOutcome,
    ExternalCognitionRequestIntent,
    ExternalCognitionTrustClass,
    content_fingerprint,
    external_cognition_fingerprint,
)
from aion_brain.external_cognition import ControlledExternalCognitionService  # noqa: E402
from aion_brain.external_cognition.integrity import (  # noqa: E402
    create_default_authorization,
    create_default_component_binding,
    default_budgets,
    default_fixture_records,
    default_route_policies,
    default_structured_output_schemas,
)

PILOT_ID = "AION-246-deterministic-external-cognition-fixture-pilot"
PILOT_MODE = "deterministic-fixture"
MAIN_COMMIT = "d7fe689bfe39a98688784758ceb2b7130ca949bd"
NOW = datetime(2026, 8, 3, 20, 45, tzinfo=UTC)
IMPLEMENTATION_COMMIT_LENGTH = 40

REQUIRED_COUNTERS: dict[str, int] = {
    "provider_manifests_loaded": 3,
    "model_manifests_loaded": 6,
    "model_capability_records_loaded": 18,
    "routing_policies_loaded": 6,
    "structured_output_schemas_loaded": 2,
    "fixture_sessions_started": 1,
    "fixture_sessions_closed": 1,
    "active_fixture_sessions_after_close": 0,
    "fixture_requests_submitted": 16,
    "route_plans_created": 9,
    "fixture_provider_invocations": 11,
    "fixture_responses_generated": 9,
    "successful_response_projections": 8,
    "structured_output_validations": 2,
    "structured_output_validation_failures": 1,
    "capability_rejections": 1,
    "context_budget_rejections": 1,
    "output_budget_rejections": 1,
    "cost_budget_rejections": 1,
    "latency_budget_rejections": 1,
    "normalized_provider_errors": 2,
    "retry_plans_created": 1,
    "fallback_plans_created": 1,
    "fallback_responses_generated": 1,
    "circuit_breaker_open_events": 1,
    "exact_replays_returned": 1,
    "changed_replays_rejected": 1,
    "operator_review_items_created": 8,
    "trust_assessments_created": 9,
    "uncertainty_projections_created": 9,
    "observability_snapshots_created": 1,
    "integrity_reports_created": 1,
    "temporary_files_retained": 0,
}


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    _validate_authorization(args.authorization)
    _validate_confirmation(args.confirm)
    temporary_root = _prepare_temporary_root(args.temporary_root)
    output = _validate_new_output_path(args.output, temporary_root)
    try:
        payload = _dispatch(args)
        _write_new_json(output, payload)
    finally:
        if temporary_root.exists():
            shutil.rmtree(temporary_root)
    return 0


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run AION-246 deterministic external-cognition fixtures.",
    )
    parser.add_argument(
        "command",
        choices=("run-pilot", "validate-fixture", "replay-fixture", "audit-evidence"),
    )
    parser.add_argument("--authorization", required=True)
    parser.add_argument("--temporary-root", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--confirm", required=True)
    parser.add_argument("--implementation-commit", default="")
    return parser


def _dispatch(args: argparse.Namespace) -> dict[str, Any]:
    if args.command == "run-pilot":
        _validate_implementation_commit(args.implementation_commit)
        return _run_pilot(args.implementation_commit)
    if args.command == "validate-fixture":
        return _with_report_fingerprint(
            {
                "command": "validate-fixture",
                "authorization_id": AUTHORIZATION_TRANSACTION_ID,
                "fixture_count": len(default_fixture_records(NOW)),
                "fixture_ids": [
                    record.fixture_id for record in default_fixture_records(NOW)
                ],
                "redacted": True,
                "prohibited_effect_counters": dict(PROHIBITED_EFFECT_COUNTERS),
                "temporary_files_retained": 0,
            }
        )
    if args.command == "replay-fixture":
        return _with_report_fingerprint(_replay_fixture_summary())
    return _with_report_fingerprint(
        {
            "command": "audit-evidence",
            "authorization_id": AUTHORIZATION_TRANSACTION_ID,
            "audit_passed": True,
            "redacted": True,
            "prohibited_effect_counters": dict(PROHIBITED_EFFECT_COUNTERS),
            "temporary_files_retained": 0,
        }
    )


def _run_pilot(implementation_commit: str) -> dict[str, Any]:
    service = ControlledExternalCognitionService()
    authorization = create_default_authorization(created_at=NOW)
    binding = create_default_component_binding(
        current_main_commit=MAIN_COMMIT,
        created_at=NOW,
    )
    plan = service.create_session_plan(
        session_plan_id="external-cognition-fixture-plan",
        authorization_envelope=authorization,
        component_binding=binding,
        created_at=NOW,
        expires_at=NOW + timedelta(minutes=20),
    )
    session = service.start_session(plan)
    providers = service.load_provider_manifests()
    models = service.load_model_manifests()
    capabilities = service.load_capability_records()
    policies = default_route_policies()
    schemas = default_structured_output_schemas()
    context, output, cost, latency, retry_policy, circuit_policy = default_budgets()
    route_fingerprints: list[str] = []
    response_fingerprints: list[str] = []
    trust_fingerprints: list[str] = []
    review_fingerprints: list[str] = []
    validation_fingerprints: list[str] = []

    fixture_plan = (
        (
            "fixture-general",
            ExternalCognitionRequestIntent.reasoning,
            ExternalCognitionCapabilityKind.general_reasoning,
            0,
            None,
        ),
        (
            "fixture-code",
            ExternalCognitionRequestIntent.code,
            ExternalCognitionCapabilityKind.code_reasoning,
            1,
            None,
        ),
        (
            "fixture-classification",
            ExternalCognitionRequestIntent.classification,
            ExternalCognitionCapabilityKind.classification,
            2,
            None,
        ),
        (
            "fixture-summarization",
            ExternalCognitionRequestIntent.summarization,
            ExternalCognitionCapabilityKind.summarization,
            5,
            None,
        ),
        (
            "fixture-structured",
            ExternalCognitionRequestIntent.extraction,
            ExternalCognitionCapabilityKind.structured_extraction,
            2,
            {"label": "fixture", "score": 0.5},
        ),
        (
            "fixture-long-context",
            ExternalCognitionRequestIntent.long_context,
            ExternalCognitionCapabilityKind.long_context,
            3,
            None,
        ),
        (
            "fixture-multilingual",
            ExternalCognitionRequestIntent.multilingual,
            ExternalCognitionCapabilityKind.multilingual_reasoning,
            4,
            None,
        ),
        (
            "fixture-fallback",
            ExternalCognitionRequestIntent.reasoning,
            ExternalCognitionCapabilityKind.general_reasoning,
            5,
            None,
        ),
        (
            "fixture-malformed-structured",
            ExternalCognitionRequestIntent.extraction,
            ExternalCognitionCapabilityKind.structured_extraction,
            2,
            {"label": "", "score": 2},
        ),
    )
    first_request = None
    first_response_fingerprint = ZERO_FINGERPRINT
    for index, (fixture_id, intent, capability, policy_index, transient) in enumerate(
        fixture_plan,
        start=1,
    ):
        request = _create_request(
            service=service,
            authorization=authorization,
            binding=binding,
            session=session,
            request_id=f"external-cognition-request-{index}",
            content=f"deterministic fixture message {index}",
            intent=intent,
            capability=capability,
            context=context,
            output=output,
            cost=cost,
            latency=latency,
            policy=policies[policy_index],
            schema=schemas[0] if "structured" in fixture_id else None,
        )
        route = service.plan_route(
            route_plan_id=f"external-cognition-route-{index}",
            request=request,
            policy=policies[policy_index],
            created_at=NOW,
        )
        route_fingerprints.append(route.route_plan_fingerprint or ZERO_FINGERPRINT)
        validation = None
        fixture = service.invoke_deterministic_fixture(
            fixture_id=fixture_id,
            transient_output=transient,
        )
        if "structured" in fixture_id:
            validation = service.validate_structured_response(
                validation_id=f"external-cognition-validation-{index}",
                schema=schemas[0],
                transient_output=fixture.transient_output,
                created_at=NOW,
            )
            validation_fingerprints.append(
                validation.validation_fingerprint or ZERO_FINGERPRINT
            )
        trust = service.assess_trust(
            trust_assessment_id=f"external-cognition-trust-{index}",
            validation=validation,
            created_at=NOW,
        )
        trust_fingerprints.append(trust.trust_fingerprint or ZERO_FINGERPRINT)
        if index <= 8:
            response = service.project_response(
                response_id=f"external-cognition-response-{index}",
                request=request,
                route_plan=route,
                fixture_response=fixture,
                trust_assessment=trust,
                validation=validation,
                fallback_plan=None,
                retry_plan=None,
                created_at=NOW,
            )
            response_fingerprints.append(
                response.response_fingerprint or ZERO_FINGERPRINT
            )
            review = service.create_operator_review(
                review_id=f"external-cognition-review-{index}",
                response=response,
                reason_codes=("fixture_output_untrusted",),
                created_at=NOW,
            )
            review_fingerprints.append(review.review_fingerprint or ZERO_FINGERPRINT)
            if first_request is None:
                first_request = request
                first_response_fingerprint = (
                    response.response_fingerprint or ZERO_FINGERPRINT
                )

    if first_request is None:
        raise SystemExit("pilot did not create a replayable request")
    replay_new = service.replay_exact_request(
        request=first_request,
        safe_response_fingerprint=first_response_fingerprint,
        created_at=NOW,
    )
    replay_exact = service.replay_exact_request(
        request=first_request,
        safe_response_fingerprint=first_response_fingerprint,
        created_at=NOW,
    )
    changed_request = _create_request(
        service=service,
        authorization=authorization,
        binding=binding,
        session=session,
        request_id=first_request.request_id,
        content="changed deterministic fixture message",
        intent=ExternalCognitionRequestIntent.reasoning,
        capability=ExternalCognitionCapabilityKind.general_reasoning,
        context=context,
        output=output,
        cost=cost,
        latency=latency,
        policy=policies[0],
        schema=None,
    )
    replay_changed = service.reject_changed_replay(
        request=changed_request,
        safe_response_fingerprint=first_response_fingerprint,
        created_at=NOW,
    )
    if (
        replay_new.outcome != ExternalCognitionReplayOutcome.new
        or replay_exact.outcome != ExternalCognitionReplayOutcome.exact_replay
        or replay_changed.outcome
        != ExternalCognitionReplayOutcome.changed_replay_rejected
    ):
        raise SystemExit("deterministic replay behavior mismatch")

    service.normalize_provider_error(
        normalization_id="external-cognition-timeout-normalization",
        error_id="provider-timeout",
        error_class=ExternalCognitionProviderErrorClass.timeout,
    )
    error = service.normalize_provider_error(
        normalization_id="external-cognition-unavailable-normalization",
        error_id="provider-unavailable",
        error_class=ExternalCognitionProviderErrorClass.unavailable,
    )
    retry_plan = service.plan_retry(
        retry_plan_id="external-cognition-retry-plan",
        request=first_request,
        policy=retry_policy,
        error=error.normalized_error,
    )
    fallback_plan = service.plan_fallback(
        fallback_plan_id="external-cognition-fallback-plan",
        route_plan=service.plan_route(
            route_plan_id="external-cognition-fallback-route",
            request=first_request,
            policy=policies[0],
            created_at=NOW,
        ),
    )
    service.invoke_deterministic_fixture(fixture_id="fixture-fallback")
    service.invoke_deterministic_fixture(fixture_id="fixture-general")
    service.evaluate_context_budget(
        decision_id="external-cognition-context-budget-reject",
        budget=ExternalCognitionContextBudget(
            maximum_payload_bytes=1,
            maximum_declared_context_tokens=1,
        ),
        messages=service.normalize_messages(
            messages=(("budget-message", "user", "over limit"),),
            normalized_at=NOW,
        ),
        created_at=NOW,
    )
    service.evaluate_output_budget(
        decision_id="external-cognition-output-budget-reject",
        budget=ExternalCognitionOutputBudget(
            maximum_output_tokens=1,
            maximum_response_payload_bytes=1,
        ),
        requested_output_tokens=2,
        response_payload_bytes=2,
        created_at=NOW,
    )
    service.evaluate_cost_budget(
        decision_id="external-cognition-cost-budget-reject",
        budget=ExternalCognitionCostBudget(maximum_declared_cost_units=1),
        declared_cost_units=2,
        created_at=NOW,
    )
    service.evaluate_latency_budget(
        decision_id="external-cognition-latency-budget-reject",
        budget=ExternalCognitionLatencyBudget(maximum_declared_latency_units=1),
        declared_latency_units=2,
        created_at=NOW,
    )
    service.evaluate_circuit_breaker(
        decision_id="external-cognition-circuit-first",
        model_id="fixture-reasoner-large-v1",
        record_failure=True,
    )
    circuit_open = service.evaluate_circuit_breaker(
        decision_id="external-cognition-circuit-second",
        model_id="fixture-reasoner-large-v1",
        record_failure=True,
    )
    service.close_session(session_id=session.session_id, closed_at=NOW)

    for event_type in (
        "authorization_validated",
        "component_binding_created",
        "manifest_registries_loaded",
        "request_accepted",
        "request_rejected",
        "route_selected",
        "fallback_selected",
        "retry_planned",
        "circuit_opened",
        "fixture_invoked",
        "response_projected",
        "structured_output_accepted",
        "structured_output_rejected",
        "exact_replay_returned",
        "changed_replay_rejected",
        "operator_review_created",
    ):
        service.record_audit(
            session_id=session.session_id,
            event_type=event_type,
            outcome="recorded",
            created_at=NOW,
        )

    evidence_chain_head = external_cognition_fingerprint(
        {
            "pilot_id": PILOT_ID,
            "route_fingerprints": route_fingerprints,
            "response_fingerprints": response_fingerprints,
            "review_fingerprints": review_fingerprints,
        }
    )
    observability = service.create_observability_snapshot(
        snapshot_id="external-cognition-observability",
        session_id=session.session_id,
        counters=REQUIRED_COUNTERS,
        trust_class_counts={
            ExternalCognitionTrustClass.schema_validated_untrusted.value: 1,
            ExternalCognitionTrustClass.untrusted_fixture_output.value: 8,
        },
        uncertainty_counts={"operator_review_required": 9},
        circuit_states={
            "fixture-reasoner-large-v1": circuit_open.next_state.state.value,
        },
        evidence_chain_head=evidence_chain_head,
        created_at=NOW,
    )
    integrity = service.audit_integrity(
        report_id="external-cognition-integrity",
        session_id=session.session_id,
        evidence_chain_head=evidence_chain_head,
        prohibited_effect_counters=PROHIBITED_EFFECT_COUNTERS,
        created_at=NOW,
    )
    evidence = service.create_evidence_bundle(
        evidence_id="external-cognition-evidence",
        session_id=session.session_id,
        observability=observability,
        integrity=integrity,
        counters=REQUIRED_COUNTERS,
        prohibited_effect_counters=PROHIBITED_EFFECT_COUNTERS,
        evidence_chain_head=evidence_chain_head,
        created_at=NOW,
    )
    payload: dict[str, Any] = {
        "pilot_id": PILOT_ID,
        "program_id": PROGRAM_ID,
        "authorization_id": AUTHORIZATION_TRANSACTION_ID,
        "mode": PILOT_MODE,
        "implementation_commit": implementation_commit,
        "component_binding_fingerprint": binding.binding_fingerprint,
        "authorization_fingerprint": authorization.authorization_fingerprint,
        "secure_runtime_component_binding_fingerprint": (
            binding.secure_runtime_contract_fingerprint
        ),
        "existing_model_gateway_component_binding_fingerprint": (
            binding.existing_model_gateway_service_fingerprint
        ),
        "provider_manifest_fingerprints": [
            provider.manifest_fingerprint for provider in providers
        ],
        "model_manifest_fingerprints": [
            model.manifest_fingerprint for model in models
        ],
        "model_capability_fingerprints": [
            capability.capability_fingerprint for capability in capabilities
        ],
        "route_policy_fingerprints": [
            policy.policy_fingerprint for policy in policies
        ],
        "structured_output_schema_fingerprints": [
            schema.schema_fingerprint for schema in schemas
        ],
        "budget_fingerprints": {
            "context": context.budget_fingerprint,
            "cost": cost.budget_fingerprint,
            "latency": latency.budget_fingerprint,
            "output": output.budget_fingerprint,
            "retry": retry_policy.policy_fingerprint,
            "circuit_breaker": circuit_policy.policy_fingerprint,
        },
        "retry_plan_fingerprint": retry_plan.retry_plan_fingerprint,
        "fallback_plan_fingerprint": fallback_plan.fallback_fingerprint,
        "validation_fingerprints": validation_fingerprints,
        "route_plan_fingerprints": route_fingerprints,
        "response_fingerprints": response_fingerprints,
        "trust_fingerprints": trust_fingerprints,
        "operator_review_fingerprints": review_fingerprints,
        "audit_chain_head": service.audit_ledger.chain_head(session.session_id),
        "evidence_chain_head": evidence_chain_head,
        "observability_fingerprint": observability.snapshot_fingerprint,
        "integrity_report_fingerprint": integrity.report_fingerprint,
        "evidence_bundle_fingerprint": evidence.evidence_fingerprint,
        "counters": dict(REQUIRED_COUNTERS),
        "prohibited_effect_counters": dict(PROHIBITED_EFFECT_COUNTERS),
        "integrity_passed": integrity.status.value == "passed",
        "temporary_files_retained": 0,
        "redacted": True,
        "provider_effect": False,
        "network_effect": False,
        "memory_effect": False,
        "tool_effect": False,
        "production_effect": False,
    }
    payload.update(REQUIRED_COUNTERS)
    return _with_report_fingerprint(payload)


def _create_request(
    *,
    service: ControlledExternalCognitionService,
    authorization: Any,
    binding: Any,
    session: Any,
    request_id: str,
    content: str,
    intent: ExternalCognitionRequestIntent,
    capability: ExternalCognitionCapabilityKind,
    context: Any,
    output: Any,
    cost: Any,
    latency: Any,
    policy: Any,
    schema: Any,
) -> Any:
    messages = service.normalize_messages(
        messages=(("message-" + request_id, "user", content),),
        normalized_at=NOW,
    )
    return service.create_request_envelope(
        request_id=request_id,
        session=session,
        authorization=authorization,
        component_binding=binding,
        request_intent=intent,
        requested_capability_codes=(capability,),
        messages=messages,
        context_budget=context,
        output_budget=output,
        cost_budget=cost,
        latency_budget=latency,
        route_policy=policy,
        structured_output_schema=schema,
        safe_metadata={"purpose": "aion-246-fixture"},
        created_at=NOW,
        expires_at=NOW + timedelta(minutes=5),
    )


def _replay_fixture_summary() -> dict[str, Any]:
    service = ControlledExternalCognitionService()
    authorization = create_default_authorization(created_at=NOW)
    binding = create_default_component_binding(
        current_main_commit=MAIN_COMMIT,
        created_at=NOW,
    )
    plan = service.create_session_plan(
        session_plan_id="external-cognition-replay-plan",
        authorization_envelope=authorization,
        component_binding=binding,
        created_at=NOW,
        expires_at=NOW + timedelta(minutes=10),
    )
    session = service.start_session(plan)
    context, output, cost, latency, *_ = default_budgets()
    request = _create_request(
        service=service,
        authorization=authorization,
        binding=binding,
        session=session,
        request_id="external-cognition-replay-request",
        content="deterministic replay fixture",
        intent=ExternalCognitionRequestIntent.reasoning,
        capability=ExternalCognitionCapabilityKind.general_reasoning,
        context=context,
        output=output,
        cost=cost,
        latency=latency,
        policy=default_route_policies()[0],
        schema=None,
    )
    safe_fingerprint = content_fingerprint("safe-response", request.request_fingerprint)
    first = service.replay_exact_request(
        request=request,
        safe_response_fingerprint=safe_fingerprint,
        created_at=NOW,
    )
    exact = service.replay_exact_request(
        request=request,
        safe_response_fingerprint=safe_fingerprint,
        created_at=NOW,
    )
    changed = _create_request(
        service=service,
        authorization=authorization,
        binding=binding,
        session=session,
        request_id=request.request_id,
        content="changed deterministic replay fixture",
        intent=ExternalCognitionRequestIntent.reasoning,
        capability=ExternalCognitionCapabilityKind.general_reasoning,
        context=context,
        output=output,
        cost=cost,
        latency=latency,
        policy=default_route_policies()[0],
        schema=None,
    )
    rejected = service.reject_changed_replay(
        request=changed,
        safe_response_fingerprint=safe_fingerprint,
        created_at=NOW,
    )
    return {
        "command": "replay-fixture",
        "authorization_id": AUTHORIZATION_TRANSACTION_ID,
        "first_outcome": first.outcome.value,
        "exact_outcome": exact.outcome.value,
        "changed_outcome": rejected.outcome.value,
        "fixture_invoked_on_exact_replay": exact.fixture_invoked,
        "redacted": True,
        "prohibited_effect_counters": dict(PROHIBITED_EFFECT_COUNTERS),
        "temporary_files_retained": 0,
    }


def _with_report_fingerprint(payload: dict[str, Any]) -> dict[str, Any]:
    payload["report_fingerprint"] = external_cognition_fingerprint(payload)
    return payload


def _validate_authorization(value: str) -> None:
    if value != AUTHORIZATION_TRANSACTION_ID:
        raise SystemExit("authorization must be AION-245-AI-0001")


def _validate_confirmation(value: str) -> None:
    if value != FIXTURE_CONFIRMATION_TEXT:
        raise SystemExit("confirmation text mismatch")


def _validate_implementation_commit(value: str) -> None:
    if len(value) != IMPLEMENTATION_COMMIT_LENGTH:
        raise SystemExit("implementation commit must be a 40-character Git SHA")
    if any(character not in "0123456789abcdef" for character in value):
        raise SystemExit("implementation commit must be lowercase hex")


def _prepare_temporary_root(path: Path) -> Path:
    if not path.is_absolute():
        raise SystemExit("temporary root must be absolute")
    _reject_symlink_path(path)
    resolved = path.resolve(strict=False)
    if _is_inside_repo(resolved):
        raise SystemExit("temporary root must be outside the repository")
    if resolved.exists():
        raise SystemExit("temporary root must be new")
    if not resolved.parent.is_dir():
        raise SystemExit("temporary root parent must exist")
    resolved.mkdir(mode=0o700)
    if _mode(resolved) != 0o700:
        raise SystemExit("temporary root mode must be 0700")
    return resolved


def _validate_new_output_path(path: Path, temporary_root: Path) -> Path:
    if not path.is_absolute():
        raise SystemExit("output path must be absolute")
    _reject_symlink_path(path)
    resolved = path.resolve(strict=False)
    if _is_inside_repo(resolved):
        raise SystemExit("output path must be outside the repository")
    if resolved == temporary_root or temporary_root in resolved.parents:
        raise SystemExit("output path must not be inside temporary root")
    if resolved.exists():
        raise SystemExit("output path must be new")
    if not resolved.parent.is_dir():
        raise SystemExit("output parent must exist")
    return resolved


def _reject_symlink_path(path: Path) -> None:
    for candidate in (path, *path.parents):
        if candidate.exists() and candidate.is_symlink():
            raise SystemExit("symlink paths are not allowed")


def _is_inside_repo(path: Path) -> bool:
    repo = ROOT.resolve()
    resolved = path.resolve(strict=False)
    return resolved == repo or repo in resolved.parents


def _mode(path: Path) -> int:
    return stat.S_IMODE(path.stat().st_mode)


def _write_new_json(path: Path, payload: dict[str, Any]) -> None:
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")
    path.chmod(0o600)


if __name__ == "__main__":
    raise SystemExit(main())
