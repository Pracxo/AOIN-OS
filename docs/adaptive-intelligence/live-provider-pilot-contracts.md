# AION-248 Live-Provider Pilot Contracts

Contract module: `services/brain-api/src/aion_brain/contracts/live_provider_pilot.py`.

The contract fixes `provider_id=openai`, `provider_api_family=responses`, `endpoint=https://api.openai.com/v1/responses`, `selected_model_id=gpt-5.6-terra`, `reasoning_effort=low`, and `maximum_live_provider_calls=6`.

Every retained record is strict Pydantic v2 data with forbidden extra fields, timezone-aware UTC timestamps, canonical fingerprints and no raw prompt, response, API key, authorization header or provider response ID.
