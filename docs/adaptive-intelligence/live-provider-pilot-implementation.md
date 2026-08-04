# AION-248 Live-Provider Pilot Implementation

AION-248 implements the AION-247-AI-0002 authorized pilot boundary for one operator-invoked OpenAI Responses API run. The installed Brain API package contains strict contracts, local validation, projection, replay, audit, observability and integrity helpers only.

The only live transport entrypoint is the uninstalled runner `scripts/live-provider-pilot-local-run.py`. It may read `OPENAI_API_KEY` from the process environment at execution time, create transient authorization headers, resolve `api.openai.com`, open TLS connections, and send exactly six synthetic text-only requests to `/v1/responses` using `gpt-5.6-terra`.

No API route, scheduler, background loop, provider SDK, request library, connector, tool execution path, file upload path, memory write path, knowledge promotion path or production runtime is added.
