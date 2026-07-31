# Model Gateway Structured Output Implementation

AION-233 supports a restricted standard-library structured-output schema
subset for deterministic local simulation only. The schema record is bounded by
`maximum_structured_output_schema_bytes=65536` and
`maximum_structured_output_depth=16`.

Allowed schema keywords are `type`, `properties`, `required`,
`additionalProperties`, `items`, `enum`, `const`, `minimum`, `maximum`,
`minLength`, `maxLength`, `minItems`, and `maxItems`. Allowed types are
`object`, `array`, `string`, `integer`, `number`, `boolean`, and `null`.

The implementation rejects external references, recursive references, dynamic
references, remote schema identifiers, executable formats, content encodings,
media types, pattern-based property execution, unknown keywords, oversized
schemas, and excessive depth. Structured-output support does not enable tool
calling, function calling, provider calls, network access, persistence, or
production execution.
