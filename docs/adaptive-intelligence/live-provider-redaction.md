# AION-248 Redaction

Committed AION-248 evidence excludes API keys, authorization headers, raw prompts, raw response text, hidden reasoning, raw provider payloads, raw provider response IDs, provider error messages, IP addresses and temporary paths.

The installed redaction helper rejects protected material in evidence and allows safe zero-state counters such as `raw_prompts_persisted=0`.
