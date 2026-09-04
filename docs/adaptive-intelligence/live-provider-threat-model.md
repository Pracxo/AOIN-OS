# AION-248 Live-Provider Threat Model

Threats covered by the pilot controls include API-key leakage, authorization-header persistence, credential-file substitution, endpoint substitution, model alias drift, redirect escape, proxy interception, DNS unsafe-address resolution, TLS downgrade, oversized responses, retries, replay amplification, tool activation, file upload, image/audio input, prompt persistence, response persistence, hidden-reasoning retention, provider output treated as fact, memory write escalation, tool execution escalation and incomplete cleanup.

The installed package contains no network-capable imports and no environment-variable access. The runner stops before DNS or transport when `OPENAI_API_KEY` is absent or empty.
