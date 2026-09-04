# v0.3 Live-Provider Retention Evidence

AION-248 requires `store=false`, `background=false`, and `stream=false` on every request. It persists no raw prompts, raw responses, hidden reasoning, provider IDs, API keys, authorization headers, resolved IP addresses or temporary paths.

Committed evidence contains fingerprints, counters, usage totals, latency summaries and disabled runtime state only.
