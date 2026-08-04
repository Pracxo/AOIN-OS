# AION-248 Checklist

- Authorization `AION-247-AI-0002` remains active for AION-248.
- Provider is exactly `openai`.
- API family is exactly `responses`.
- Endpoint is exactly `https://api.openai.com/v1/responses`.
- Model is exactly `gpt-5.6-terra`.
- Installed package has no DNS, TLS, HTTP or environment access.
- Uninstalled runner stops before DNS or transport when `OPENAI_API_KEY` is absent.
- Unit tests use mocked/fake transport only.
- No tools, files, images, audio, previous response, memory write, connector, action or production effect is authorized.
