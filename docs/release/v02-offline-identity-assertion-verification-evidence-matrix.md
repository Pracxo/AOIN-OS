# v0.2 Offline Identity Assertion Verification Evidence Matrix

| Evidence | Location |
| --- | --- |
| Contract tests | `services/brain-api/tests/test_identity_assertion_contracts.py` |
| Base64url tests | `services/brain-api/tests/test_identity_assertion_base64url.py` |
| Canonical payload tests | `services/brain-api/tests/test_identity_assertion_canonical_payload.py` |
| Registry tests | `services/brain-api/tests/test_trusted_public_key_registry.py` |
| Verifier tests | `services/brain-api/tests/test_offline_identity_assertion_verifier.py` |
| Negative crypto tests | `services/brain-api/tests/test_identity_assertion_negative_crypto.py` |
| Runtime boundary tests | `services/brain-api/tests/test_identity_assertion_no_runtime_integration.py` |
| Replay boundary tests | `services/brain-api/tests/test_identity_assertion_replay_boundary.py` |
| Concurrency tests | `services/brain-api/tests/test_identity_assertion_concurrency.py` |
| Performance smoke | `services/brain-api/tests/test_identity_assertion_performance.py` |
| No-go gate | `scripts/production-auth-offline-identity-assertion-no-go-regression.sh` |
| Runtime hold gate | `scripts/production-auth-offline-identity-assertion-runtime-hold.sh` |
