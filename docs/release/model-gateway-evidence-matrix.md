# Model Gateway Evidence Matrix

| Evidence | Location | Result |
| --- | --- | --- |
| Implementation docs | `docs/secure-runtime-integration/model-gateway-implementation.md` | Implemented pending AION-234 closeout |
| Contracts | `services/brain-api/src/aion_brain/contracts/model_gateway.py` | Strict Pydantic v2 contracts |
| Service orchestration | `services/brain-api/src/aion_brain/model_gateway/provider_adapter.py` | Controlled local simulation only |
| Provider registry | `services/brain-api/src/aion_brain/model_gateway/manifests.py` | Closed provider allowlist |
| Model registry | `services/brain-api/src/aion_brain/model_gateway/manifests.py` | Closed model allowlist |
| Runner | `scripts/model-gateway-local-simulation-run.py` | Uninstalled local runner |
| Pilot evidence | `examples/secure-runtime-integration/model-gateway-local-simulation-pilot-evidence.json` | Passed with zero prohibited effects |
| Static console evidence | `operator-console-static/demo-data/model-gateway-static-console-evidence.json` | Redacted read-only evidence |
| Contract examples | `examples/secure-runtime-integration/model-gateway-contract-examples.json` | Public contract examples |
| No-go gate | `scripts/model-gateway-no-go-regression.sh` | Preserves no-live-provider boundary |
| Implementation gate | `scripts/model-gateway-check.sh` | Verifies AION-233 implementation |
| Pilot gate | `scripts/model-gateway-pilot-evidence-check.sh` | Verifies pilot counters and fingerprint |
| Runtime hold | `scripts/model-gateway-runtime-hold.sh` | Holds live runtime disabled |
