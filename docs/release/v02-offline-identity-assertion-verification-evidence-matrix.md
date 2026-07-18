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


## AION-163 Replay Protection Authorization Update

AION-163 records AION-162 PR #72 and corrective PR #73 as the completed offline verification delivery, closes `AION-161-PA-0006` as inactive, consumed, expired, and non-reusable, and creates `AION-163-PA-0007` as the sole active authorization for AION-164 persistent identity-assertion replay protection. The next critical path is AION-164. Runtime request authentication, ActorContext application, RequestIdentityContext application, dependency changes, migrations, production schema auto-create, package files, lockfiles, v0.2 tags, and v0.2 releases remain blocked.
