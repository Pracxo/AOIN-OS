# Model Gateway Message Normalization

Message normalization accepts raw message content only as a transient function argument. Retained message records contain role, content fingerprint, UTF-8 byte count, deterministic token estimate, redaction state, protected-material result, timestamp, and message fingerprint.

System override markers, execution requests, protected material, credentials, API keys, tokens, cookies, authorization headers, hidden reasoning, raw prompts, tool calls, and function calls are rejected before routing.
