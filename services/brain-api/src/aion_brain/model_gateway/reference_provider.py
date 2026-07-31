"""Deterministic reference provider for simulation-only model output."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime
from typing import Any

from aion_brain.contracts.model_gateway import (
    DETERMINISTIC_PROVIDER_ID,
    REFERENCE_JSON_MODEL_ID,
    REFERENCE_TEXT_MODEL_ID,
    ZERO_FINGERPRINT,
    ModelGatewayOperation,
    ModelGatewayOutputMode,
    ModelGatewayReferenceProviderRequest,
    ModelGatewayReferenceProviderResponse,
    ModelStructuredOutputSchema,
    content_fingerprint,
    estimate_tokens_from_bytes,
    model_gateway_fingerprint,
)


class DeterministicReferenceModelProvider:
    """Local deterministic provider with no live-send operation."""

    provider_id = DETERMINISTIC_PROVIDER_ID

    def validate_adapter_state(self) -> bool:
        """Return true when the provider remains local and simulation-only."""

        return True

    def adapter_manifest(self) -> dict[str, object]:
        """Return redacted adapter metadata without endpoints or credentials."""

        return {
            "provider_id": self.provider_id,
            "simulation_only": True,
            "actual_provider_call": False,
            "network_effect": False,
            "credential_effect": False,
        }

    def simulate(
        self,
        *,
        reference_request: ModelGatewayReferenceProviderRequest,
        structured_schema: ModelStructuredOutputSchema | None,
        created_at: datetime,
    ) -> ModelGatewayReferenceProviderResponse:
        """Return deterministic synthetic output derived from fingerprints only."""

        if reference_request.model_id == REFERENCE_TEXT_MODEL_ID:
            output: str | dict[str, Any] = _text_output(reference_request)
            mode = ModelGatewayOutputMode.text
        elif reference_request.model_id == REFERENCE_JSON_MODEL_ID:
            if reference_request.output_mode == ModelGatewayOutputMode.structured_json:
                output = _structured_output(reference_request, structured_schema)
                mode = ModelGatewayOutputMode.structured_json
            else:
                output = _text_output(reference_request)
                mode = ModelGatewayOutputMode.text
        else:
            raise ValueError("unknown reference model")
        encoded = _output_bytes(output)
        return ModelGatewayReferenceProviderResponse(
            response_id=f"response-{reference_request.reference_request_id}",
            provider_id=DETERMINISTIC_PROVIDER_ID,
            model_id=reference_request.model_id,
            request_fingerprint=reference_request.request_fingerprint,
            output_fingerprint=content_fingerprint("reference_provider_output", encoded),
            output_mode=mode,
            output_byte_count=len(encoded),
            estimated_output_tokens=estimate_tokens_from_bytes(len(encoded)),
            created_at=created_at,
            transient_output=output,
        )


def build_reference_provider_request(
    *,
    reference_request_id: str,
    model_id: str,
    request_fingerprint: str,
    operation: ModelGatewayOperation,
    output_mode: ModelGatewayOutputMode,
    requested_output_tokens: int,
    structured_schema: ModelStructuredOutputSchema | None,
    created_at: datetime,
) -> ModelGatewayReferenceProviderRequest:
    """Build a fingerprint-only reference-provider request."""

    structured_schema_fingerprint = ZERO_FINGERPRINT
    if structured_schema is not None:
        schema_fingerprint = structured_schema.schema_fingerprint
        if schema_fingerprint is None:
            raise ValueError("structured schema fingerprint missing")
        structured_schema_fingerprint = schema_fingerprint

    return ModelGatewayReferenceProviderRequest(
        reference_request_id=reference_request_id,
        provider_id=DETERMINISTIC_PROVIDER_ID,
        model_id=model_id,
        request_fingerprint=request_fingerprint,
        operation=operation,
        output_mode=output_mode,
        requested_output_tokens=requested_output_tokens,
        structured_schema_fingerprint=structured_schema_fingerprint,
        created_at=created_at,
    )


def _text_output(request: ModelGatewayReferenceProviderRequest) -> str:
    digest = model_gateway_fingerprint(
        {
            "model_id": request.model_id,
            "operation": request.operation.value,
            "request_fingerprint": request.request_fingerprint,
        }
    )
    return (
        "synthetic untrusted reference output "
        f"{digest[:24]} simulation_only no_external_knowledge"
    )


def _structured_output(
    request: ModelGatewayReferenceProviderRequest,
    schema: ModelStructuredOutputSchema | None,
) -> dict[str, Any]:
    if schema is None:
        raise ValueError("structured schema required")
    seed = model_gateway_fingerprint(
        {
            "request": request.request_fingerprint,
            "schema": schema.schema_fingerprint,
        }
    )
    generated = _value_for_schema(schema.schema_definition, seed)
    if not isinstance(generated, dict):
        raise ValueError("structured reference output root must be object")
    return generated


def _value_for_schema(schema: Mapping[str, Any], seed: str) -> Any:
    declared = schema.get("type")
    if isinstance(declared, list):
        declared = declared[0]
    if "const" in schema:
        return schema["const"]
    if "enum" in schema and isinstance(schema["enum"], list) and schema["enum"]:
        return schema["enum"][0]
    if declared == "object":
        properties = schema.get("properties", {})
        required = set(schema.get("required", []))
        result: dict[str, Any] = {}
        if isinstance(properties, Mapping):
            for name in sorted(properties):
                if name in required or not required:
                    nested = properties[name]
                    if isinstance(nested, Mapping):
                        result[name] = _value_for_schema(nested, seed + name)
        result.setdefault("synthetic", True)
        result.setdefault("trust", "untrusted")
        return result
    if declared == "array":
        items = schema.get("items")
        if isinstance(items, Mapping):
            return [_value_for_schema(items, seed)]
        return []
    if declared == "integer":
        return int(seed[:6], 16) % 100
    if declared == "number":
        return round((int(seed[:6], 16) % 1000) / 100, 2)
    if declared == "boolean":
        return int(seed[:2], 16) % 2 == 0
    if declared == "null":
        return None
    return f"synthetic-{seed[:12]}"


def _output_bytes(output: object) -> bytes:
    return model_gateway_fingerprint({"output": output}).encode("utf-8")
