# Operator Console API Examples

Examples live in `examples/operator-console/` and are synthetic. They show the
read-only contract shape for future consumers.

## Example Files

- `view-model-request.json`
- `console-audit-request.json`
- `overview-view-model-example.json`
- `module-lifecycle-view-model-example.json`
- `provider-hardening-view-model-example.json`

## API Paths

- `GET /brain/operator-console/views`
- `POST /brain/operator-console/view-model`
- `POST /brain/operator-console/audit`
- `GET /brain/operator-console/workflows`
- `GET /brain/operator-console/demo-map`

All examples preserve no runtime UI, no raw prompt exposure, no hidden reasoning
exposure, no secret exposure, no activation, and no execution.

## Static Prototype Demo Data

AION-089 adds local demo JSON under `operator-console-static/demo-data/`.
Those files mirror the read-only view-model shape for offline rendering. They
are synthetic, redacted, and include forbidden action descriptors only.

The static prototype uses the existing
`POST /brain/operator-console/view-model` API when the API base is local and
reachable. It does not introduce a new API path.
