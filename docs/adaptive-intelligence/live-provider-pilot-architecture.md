# AION-248 Live-Provider Pilot Architecture Boundary

AION-247 authorizes but does not implement one future operator-invoked OpenAI Responses API pilot for AION-248.

The future pilot is limited to one provider, one explicitly selected GPT-5.6 model, one endpoint host `api.openai.com`, one endpoint path `/v1/responses`, method `POST`, process-environment credential input from `OPENAI_API_KEY`, TLS certificate verification, no redirects, no proxy inheritance, `store=false`, `background=false`, `stream=false`, no tools, no files, no previous response continuation, synthetic text only and at most six live provider calls.

AION-247 creates no `live_provider_pilot` runtime package, no provider adapter, no HTTP client dependency, no API route, no credential store and no token store.
