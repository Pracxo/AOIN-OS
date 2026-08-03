# AION-246 External Cognition Gateway Scope

AION-246 is authorized to create a controlled provider-neutral external-cognition gateway foundation using deterministic fixtures only.

## Authorized Future Source Scope

- `services/brain-api/src/aion_brain/contracts/external_cognition.py`
- `services/brain-api/src/aion_brain/external_cognition/__init__.py`
- `services/brain-api/src/aion_brain/external_cognition/authorization.py`
- `services/brain-api/src/aion_brain/external_cognition/component_binding.py`
- `services/brain-api/src/aion_brain/external_cognition/provider_manifest.py`
- `services/brain-api/src/aion_brain/external_cognition/model_manifest.py`
- `services/brain-api/src/aion_brain/external_cognition/request_envelope.py`
- `services/brain-api/src/aion_brain/external_cognition/response_envelope.py`
- `services/brain-api/src/aion_brain/external_cognition/message_normalization.py`
- `services/brain-api/src/aion_brain/external_cognition/structured_output.py`
- `services/brain-api/src/aion_brain/external_cognition/routing_policy.py`
- `services/brain-api/src/aion_brain/external_cognition/budgets.py`
- `services/brain-api/src/aion_brain/external_cognition/trust.py`
- `services/brain-api/src/aion_brain/external_cognition/redaction.py`
- `services/brain-api/src/aion_brain/external_cognition/circuit_breaker.py`
- `services/brain-api/src/aion_brain/external_cognition/fixture_provider.py`
- `services/brain-api/src/aion_brain/external_cognition/replay.py`
- `services/brain-api/src/aion_brain/external_cognition/observability.py`
- `services/brain-api/src/aion_brain/external_cognition/audit.py`
- `services/brain-api/src/aion_brain/external_cognition/integrity.py`
- `services/brain-api/src/aion_brain/external_cognition/evidence.py`
- `scripts/external-cognition-fixture-local-run.py`

## Prohibited Source Scope

AION-246 may not create `network.py`, `http_client.py`, provider-specific adapters, credential stores, token stores, background workers, schedulers, or API runtime routes.

AION-245 creates none of the AION-246 source files. Their absence is part of the current runtime hold.
