"""Response validation, untrusted classification, and provenance."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from aion_brain.contracts.model_gateway import (
    MAXIMUM_RESPONSE_BYTES_PER_REQUEST,
    ModelGatewayReferenceProviderResponse,
    ModelGatewayRequestEnvelope,
    ModelGatewayResponseClassification,
    ModelGatewayResponseValidationStatus,
    ModelGatewayRouteDisposition,
    ModelManifest,
    ModelOutputProvenance,
    ModelOutputTrustClass,
    ModelOutputValidationResult,
    ModelProviderManifest,
    ModelRoutingPlan,
    ModelStructuredOutputSchema,
    contains_executable_content,
    contains_production_action_marker,
    contains_tool_or_function_smuggling,
    content_fingerprint,
    estimate_tokens_from_bytes,
    reject_gateway_protected_material,
)


def validate_response(
    *,
    validation_id: str,
    request: ModelGatewayRequestEnvelope,
    provider_manifest: ModelProviderManifest,
    model_manifest: ModelManifest,
    route_plan: ModelRoutingPlan,
    response: ModelGatewayReferenceProviderResponse,
    transient_output: Any,
    structured_schema: ModelStructuredOutputSchema | None,
    created_at: datetime,
) -> ModelOutputValidationResult:
    """Validate a transient reference-provider output and retain only fingerprints."""

    reason_codes: list[str] = []
    if request.request_fingerprint != response.request_fingerprint:
        reason_codes.append("request_fingerprint_mismatch")
    if route_plan.disposition != ModelGatewayRouteDisposition.selected:
        reason_codes.append("route_not_selected")
    if route_plan.selected_model_id != response.model_id:
        reason_codes.append("model_route_mismatch")
    if response.output_byte_count > MAXIMUM_RESPONSE_BYTES_PER_REQUEST:
        reason_codes.append("response_bytes_exceeded")
    if response.estimated_output_tokens > request.requested_output_tokens:
        reason_codes.append("response_tokens_exceeded")
    try:
        reject_gateway_protected_material({"output": transient_output})
    except ValueError:
        reason_codes.append("protected_material_detected")
    if contains_tool_or_function_smuggling(transient_output):
        reason_codes.append("smuggled_tool_or_function_call")
    if contains_executable_content(transient_output):
        reason_codes.append("executable_content_detected")
    if contains_production_action_marker(transient_output):
        reason_codes.append("production_action_marker_detected")
    if structured_schema is not None and not isinstance(transient_output, dict):
        reason_codes.append("structured_output_not_object")
    status = (
        ModelGatewayResponseValidationStatus.passed
        if not reason_codes
        else ModelGatewayResponseValidationStatus.blocked
    )
    return ModelOutputValidationResult(
        validation_id=validation_id,
        request_fingerprint=request.request_fingerprint or "",
        provider_manifest_fingerprint=provider_manifest.manifest_fingerprint or "",
        model_manifest_fingerprint=model_manifest.manifest_fingerprint or "",
        route_plan_fingerprint=route_plan.plan_fingerprint or "",
        response_fingerprint=response.response_fingerprint or "",
        output_mode=response.output_mode,
        status=status,
        reason_codes=tuple(reason_codes or ("response_validated",)),
        created_at=created_at,
    )


def classify_untrusted_output(
    *,
    classification_id: str,
    response: ModelGatewayReferenceProviderResponse,
    validation: ModelOutputValidationResult,
    created_at: datetime,
) -> ModelGatewayResponseClassification:
    """Classify every model output as untrusted."""

    if validation.status != ModelGatewayResponseValidationStatus.passed:
        trust = ModelOutputTrustClass.untrusted_blocked
    elif response.output_mode.value == "structured_json":
        trust = ModelOutputTrustClass.untrusted_validated_structured
    else:
        trust = ModelOutputTrustClass.untrusted_validated_text
    return ModelGatewayResponseClassification(
        classification_id=classification_id,
        output_trust_class=trust,
        response_fingerprint=response.response_fingerprint or "",
        validation_fingerprint=validation.validation_fingerprint or "",
        created_at=created_at,
    )


def build_output_provenance(
    *,
    provenance_id: str,
    provider_manifest: ModelProviderManifest,
    model_manifest: ModelManifest,
    request: ModelGatewayRequestEnvelope,
    route_plan: ModelRoutingPlan,
    response: ModelGatewayReferenceProviderResponse,
    validation: ModelOutputValidationResult,
    classification: ModelGatewayResponseClassification,
    audit_chain_head: str,
    created_at: datetime,
) -> ModelOutputProvenance:
    """Build redacted output provenance with no prompt or response body."""

    return ModelOutputProvenance(
        provenance_id=provenance_id,
        provider_id=provider_manifest.provider_id,
        provider_manifest_fingerprint=provider_manifest.manifest_fingerprint or "",
        model_id=model_manifest.model_id,
        model_manifest_fingerprint=model_manifest.manifest_fingerprint or "",
        request_fingerprint=request.request_fingerprint or "",
        routing_plan_fingerprint=route_plan.plan_fingerprint or "",
        response_fingerprint=response.response_fingerprint or "",
        validation_result_fingerprint=validation.validation_fingerprint or "",
        output_classification=classification.output_trust_class,
        redacted=True,
        audit_chain_head=audit_chain_head,
        created_at=created_at,
    )


def transient_output_fingerprint(transient_output: object) -> str:
    """Return the retained output fingerprint without retaining raw output."""

    return content_fingerprint("model_gateway_transient_output", str(transient_output))


def transient_output_token_estimate(transient_output: object) -> int:
    """Return deterministic token estimate for a transient output."""

    return estimate_tokens_from_bytes(str(transient_output).encode("utf-8").__len__())
