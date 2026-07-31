"""Message normalization and model-gateway budget decisions."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime

from aion_brain.contracts.model_gateway import (
    ModelGatewayContextBudget,
    ModelGatewayContextBudgetDecision,
    ModelGatewayContextItem,
    ModelGatewayContextUsage,
    ModelGatewayMessage,
    ModelGatewayMessageRole,
    ModelGatewaySystemInstructionPolicyBinding,
    ModelGatewayTokenBudget,
    ModelGatewayTokenBudgetDecision,
    ModelGatewayTokenUsage,
    content_fingerprint,
    copy_redacted_mapping,
    ensure_gateway_identifier,
    ensure_gateway_utc,
    estimate_tokens_from_bytes,
    local_model_gateway_confirmation_fingerprint,
    model_gateway_fingerprint,
    reject_gateway_protected_material,
)

SYSTEM_POLICY_BODIES: Mapping[str, str] = {
    "aion-safe-text-simulation-v1": (
        "AION model gateway text simulation policy: produce synthetic, untrusted, "
        "non-executable, no-tool, no-memory output."
    ),
    "aion-safe-structured-simulation-v1": (
        "AION model gateway structured simulation policy: produce schema-bounded, "
        "synthetic, untrusted JSON with no tool or function call fields."
    ),
}
SYSTEM_OVERRIDE_MARKERS = (
    "ignore previous",
    "ignore system",
    "override system",
    "replace system",
)
EXECUTION_REQUEST_MARKERS = (
    "run shell",
    "execute command",
    "call tool",
    "function call",
    "tool call",
)


def normalize_model_gateway_message(
    *,
    message_id: str,
    role: ModelGatewayMessageRole | str,
    content: str,
    created_at: datetime,
) -> ModelGatewayMessage:
    """Normalize a transient message into a redacted retained record."""

    ensure_gateway_identifier(message_id, field_name="message_id")
    _reject_message_content(content)
    encoded = content.encode("utf-8")
    return ModelGatewayMessage(
        message_id=message_id,
        role=ModelGatewayMessageRole(role),
        content_fingerprint=content_fingerprint("model_gateway_message", content),
        utf8_byte_count=len(encoded),
        deterministic_token_estimate=estimate_tokens_from_bytes(len(encoded)),
        created_at=ensure_gateway_utc(created_at),
    )


def normalize_model_gateway_context_item(
    *,
    context_item_id: str,
    context_kind: str,
    source: str,
    content: str,
) -> ModelGatewayContextItem:
    """Normalize transient context into a redacted retained record."""

    ensure_gateway_identifier(context_item_id, field_name="context_item_id")
    ensure_gateway_identifier(context_kind, field_name="context_kind")
    reject_gateway_protected_material({"source": source, "content": content})
    encoded = content.encode("utf-8")
    return ModelGatewayContextItem(
        context_item_id=context_item_id,
        context_kind=context_kind,
        source_fingerprint=content_fingerprint("model_gateway_context_source", source),
        content_fingerprint=content_fingerprint("model_gateway_context", content),
        utf8_byte_count=len(encoded),
        deterministic_token_estimate=estimate_tokens_from_bytes(len(encoded)),
    )


def bind_system_instruction_policy(
    *, policy_code: str, created_at: datetime
) -> ModelGatewaySystemInstructionPolicyBinding:
    """Bind a closed system policy by fingerprint."""

    if policy_code not in SYSTEM_POLICY_BODIES:
        raise ValueError("unknown model-gateway system policy")
    return ModelGatewaySystemInstructionPolicyBinding(
        policy_code=policy_code,
        policy_body_fingerprint=content_fingerprint(
            "system_instruction_policy",
            SYSTEM_POLICY_BODIES[policy_code],
        ),
        created_at=ensure_gateway_utc(created_at),
    )


def evaluate_context_budget(
    *,
    decision_id: str,
    budget: ModelGatewayContextBudget,
    usage: ModelGatewayContextUsage,
    created_at: datetime,
) -> ModelGatewayContextBudgetDecision:
    """Evaluate context budgets and fail closed on any one-over-limit value."""

    violations = []
    if usage.message_count > budget.maximum_messages_per_request:
        violations.append("message_count_exceeded")
    if usage.context_item_count > budget.maximum_context_items_per_request:
        violations.append("context_item_count_exceeded")
    if usage.prompt_utf8_bytes > budget.maximum_prompt_bytes_per_request:
        violations.append("prompt_bytes_exceeded")
    if usage.context_utf8_bytes > budget.maximum_context_bytes_per_request:
        violations.append("context_bytes_exceeded")
    if usage.response_byte_limit > budget.maximum_response_bytes_per_request:
        violations.append("response_bytes_exceeded")
    if usage.structured_schema_bytes > budget.maximum_structured_output_schema_bytes:
        violations.append("structured_schema_bytes_exceeded")
    if usage.structured_schema_depth > budget.maximum_structured_output_depth:
        violations.append("structured_schema_depth_exceeded")
    return ModelGatewayContextBudgetDecision(
        decision_id=decision_id,
        budget=budget,
        usage=usage,
        allowed=not violations,
        reason_codes=tuple(violations or ("context_budget_passed",)),
        created_at=ensure_gateway_utc(created_at),
    )


def evaluate_token_budget(
    *,
    decision_id: str,
    budget: ModelGatewayTokenBudget,
    usage: ModelGatewayTokenUsage,
    created_at: datetime,
) -> ModelGatewayTokenBudgetDecision:
    """Evaluate deterministic token-estimate budgets."""

    violations = []
    if usage.estimated_input_tokens > budget.maximum_input_tokens_per_request:
        violations.append("input_tokens_exceeded")
    if usage.requested_output_tokens > budget.maximum_output_tokens_per_request:
        violations.append("output_tokens_exceeded")
    if usage.estimated_session_tokens_after_request > budget.maximum_total_tokens_per_session:
        violations.append("session_tokens_exceeded")
    if usage.provider_native_tokenizer_used:
        violations.append("provider_native_tokenizer_used")
    return ModelGatewayTokenBudgetDecision(
        decision_id=decision_id,
        budget=budget,
        usage=usage,
        allowed=not violations,
        reason_codes=tuple(violations or ("token_budget_passed",)),
        created_at=ensure_gateway_utc(created_at),
    )


def safe_metadata_fingerprint(metadata: Mapping[str, object] | None) -> str:
    """Return a fingerprint for safe metadata without retaining payload content."""

    payload = copy_redacted_mapping(metadata or {})
    return model_gateway_fingerprint({"metadata": payload})


def confirmation_fingerprint() -> str:
    """Expose the required local simulation confirmation fingerprint."""

    return local_model_gateway_confirmation_fingerprint()


def _reject_message_content(content: str) -> None:
    reject_gateway_protected_material({"message": content})
    lowered = content.lower()
    if any(marker in lowered for marker in SYSTEM_OVERRIDE_MARKERS):
        raise ValueError("system policy override is not allowed")
    if any(marker in lowered for marker in EXECUTION_REQUEST_MARKERS):
        raise ValueError("execution request is not allowed")
