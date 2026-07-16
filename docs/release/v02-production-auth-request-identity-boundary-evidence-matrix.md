# v0.2 Production Auth Request Identity Boundary Evidence Matrix

| Evidence | File | State |
| --- | --- | --- |
| Contracts | `services/brain-api/src/aion_brain/contracts/request_identity.py` | strict, fingerprinted, disabled |
| Verifier | `services/brain-api/src/aion_brain/production_auth/verifier.py` | provider-agnostic, disabled |
| Boundary | `services/brain-api/src/aion_brain/production_auth/request_boundary.py` | consumes safe correlation only |
| Middleware | `services/brain-api/src/aion_brain/production_auth/request_middleware.py` | observe-only request-state attachment |
| Evidence builders | `services/brain-api/src/aion_brain/production_auth/request_evidence.py` | redacted audit and provenance |
| Config | `services/brain-api/src/aion_brain/config.py` | false default |
| App factory | `services/brain-api/src/aion_brain/kernel/app_factory.py` | optional registration |
| Tests | `services/brain-api/tests/test_request_identity_*.py` | focused coverage |
| Static evidence | `operator-console-static/demo-data/production-auth-request-identity-boundary.json` | read-only |
| Runtime hold | `operator-console-static/demo-data/production-auth-request-identity-runtime-hold.json` | read-only |
| Gate | `scripts/production-auth-request-identity-check.sh` | local validation |
| No-go | `scripts/production-auth-request-identity-no-go-regression.sh` | prohibited-surface scan |

Authorization lineage: `AION-155-PA-0003` consumed by `AION-156`.
