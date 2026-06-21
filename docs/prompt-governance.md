# Prompt Packet and Model Input Governance

AION Prompt Packet Compiler is the Brain-owned boundary for preparing
provider-neutral model input. It compiles system boundaries, policy and
autonomy constraints, instruction resolution output, user messages, retrieved
context, memory recall, evidence, beliefs, grounding metadata, citations,
templates, and fragments into a structured prompt packet.

This layer does not decide policy, approve actions, execute tools, expand
autonomy, create truth, optimize prompts with a model, or call external model
providers. External providers consume compiled packets only through the Model
Gateway.

## Core Concepts

- `PromptSection` is one ordered, typed input section with explicit trust.
- `PromptTemplate` is a provider-neutral reusable section bundle.
- `PromptFragment` is a reusable safe instruction fragment.
- `PromptPacket` is a metadata-first compiled packet with section manifests,
  hashes, constraints, redacted preview, token estimate, and boundary refs.
- `PromptBoundaryCheck` records deterministic boundary validation.
- `PromptInjectionFinding` records deterministic injection findings with
  redacted matched text only.
- `ModelInputManifest` records the provider-neutral model input handoff using
  hashes, section counts, budgets, grounding refs, instruction refs, and safety
  refs.
- `PromptPreview` exposes safe, metadata-only, or hashes-only views. It never
  exposes hidden reasoning, raw prompts, or raw secrets.

## Trust Boundaries

Retrieved context is treated as `untrusted_context` unless a trusted AION
contract explicitly says otherwise. Memory sections must be labeled
`memory_recall` because recall is not truth. Evidence, belief, grounding, and
citation sections remain references and support metadata, not new truth.

The boundary guard checks that system, policy, autonomy, risk, and approval
constraints cannot be overridden by user or retrieved content. High and
critical injection findings block prompt compilation when
`AION_PROMPT_INJECTION_BLOCK_HIGH_SEVERITY=true`.

## Storage Rules

Raw rendered prompts are not persisted by default. With
`AION_PROMPT_STORE_RENDERED_TEXT=false`, the repository stores section
manifests, hashes, redacted previews, constraints, and metadata only. Hidden
reasoning, chain-of-thought, provider-specific hidden prompt syntax, raw
headers, and secret-like values are rejected or redacted before persistence.

## APIs

- `POST /brain/prompts/templates`
- `GET /brain/prompts/templates`
- `GET /brain/prompts/templates/{prompt_template_id}`
- `POST /brain/prompts/templates/{prompt_template_id}/disable`
- `POST /brain/prompts/templates/seed-defaults`
- `POST /brain/prompts/fragments`
- `GET /brain/prompts/fragments`
- `POST /brain/prompts/compile`
- `GET /brain/prompts/packets/{prompt_packet_id}`
- `GET /brain/prompts/packets`
- `POST /brain/prompts/preview`
- `POST /brain/prompts/boundary-check`
- `GET /brain/prompts/injection-findings`
- `GET /brain/prompts/model-input-manifests/{model_input_manifest_id}`
- `GET /brain/prompts/model-input-manifests`

## SDK and CLI

`client.prompts` exposes template, fragment, compile, preview, boundary check,
injection finding, packet, and manifest helpers. The SDK calls public Brain
APIs only and does not import `aion_brain`.

CLI examples:

```bash
./scripts/aionctl.sh prompts compile --user-message "Answer generically."
./scripts/aionctl.sh prompts preview --prompt-packet-id prompt-packet-id
./scripts/aionctl.sh prompts templates list
./scripts/aionctl.sh prompts templates seed
./scripts/aionctl.sh prompts fragments list
./scripts/aionctl.sh prompts boundary-check --prompt-packet-id prompt-packet-id
./scripts/aionctl.sh prompts injection-findings
./scripts/aionctl.sh prompts manifests
```

AION v0.1 prompt packets are provider-neutral and governed. Raw rendered
prompts are not persisted by default.
