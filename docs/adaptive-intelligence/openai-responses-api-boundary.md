# OpenAI Responses API Boundary

AION-248 permits one endpoint only: `POST https://api.openai.com/v1/responses`. The selected model is `gpt-5.6-terra`; model listing, endpoint discovery, aliases and model substitution are rejected.

The installed package cannot perform HTTP, DNS, TLS or environment access. The uninstalled runner uses standard-library HTTPS only, rejects redirects, bypasses proxy-aware clients, and closes each connection after one request.
