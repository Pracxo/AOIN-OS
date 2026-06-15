# Security Hygiene

- Do not store raw secrets.
- Do not commit `.env`.
- Do not expose stack traces in API responses.
- Do not write raw prompts to logs.
- Do not store raw request bodies in audit records.
- Do not add shell execution.
- Do not add Docker execution in v0.1.
- Do not make external connector calls in v0.1.
- Keep policy fail-closed.
- Keep autonomy disabled, observe-only, assistive, or dry-run by default.
- Keep tests free of external network requirements.
