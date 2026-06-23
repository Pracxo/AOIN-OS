# Model Provider Hardening

AION-086 adds a provider-readiness layer before any real model provider can be
enabled. The layer is Brain-owned, metadata-only, local, deterministic, and
dry-run by default.

It owns:

- provider profiles
- prompt egress previews
- dry-run provider simulations
- provider readiness assessments
- provider blockers
- aggregate provider-hardening queries

It does not call model providers, send prompts externally, store provider
credentials, persist prompt bodies, execute tools, enable providers, or bypass
prompt/output/grounding/audit/operator gates.

## API

- `POST /brain/model-providers/profiles`
- `GET /brain/model-providers/profiles`
- `GET /brain/model-providers/profiles/{provider_profile_id}`
- `POST /brain/model-providers/profiles/seed-defaults`
- `POST /brain/model-providers/egress-preview`
- `POST /brain/model-providers/simulate`
- `POST /brain/model-providers/readiness`
- `GET /brain/model-providers/blockers`
- `POST /brain/model-providers/blockers/{provider_blocker_id}/dismiss`
- `POST /brain/model-providers/query`

## Safety Boundary

A provider profile is not provider activation. A readiness assessment is not
provider enablement. A dry-run simulation is not a model invocation. A prompt
egress preview is not prompt transmission.

The default settings keep `AION_EXTERNAL_MODEL_CALLS_ENABLED=false` and
`AION_MODEL_PROVIDER_CREDENTIALS_ENABLED=false`.

## Operator Console Mapping

AION-087 maps provider hardening into a future Operator Console view. The view
may show provider profiles, prompt egress preview summaries, dry-run
simulations, readiness state, and blockers.

The view must not transmit prompts, store provider credentials, call model
providers, enable external model calls, reveal raw prompts, expose hidden
reasoning, reveal secrets, expose raw provider payloads, or enable providers.
