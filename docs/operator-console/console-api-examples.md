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
