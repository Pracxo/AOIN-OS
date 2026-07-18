# v0.2 Identity Assertion Replay Protection Evidence Matrix

| Requirement | Evidence |
| --- | --- |
| Replay key uses issuer plus assertion ID | `test_identity_assertion_replay_key.py` |
| Dedicated SQLAlchemy table | `test_identity_assertion_replay_table_contract.py` |
| Insert-first claim | `test_identity_assertion_replay_repository_claim.py` |
| Concurrent duplicate claims | `test_identity_assertion_replay_repository_concurrency.py` |
| Multiple engines | `test_identity_assertion_replay_multiple_engines.py` |
| Replay service outcomes | `test_identity_assertion_replay_service.py` |
| Pipeline ordering | `test_identity_assertion_replay_pipeline.py` |
| Retention and cleanup | `test_identity_assertion_replay_retention.py`, `test_identity_assertion_replay_cleanup.py`, `test_identity_assertion_replay_cleanup_race.py` |
| Fail-closed repository behavior | `test_identity_assertion_replay_failure_safety.py` |
| Redacted evidence | `test_identity_assertion_replay_evidence.py`, `test_identity_assertion_replay_redaction.py` |
| No runtime integration | `test_identity_assertion_replay_no_runtime_integration.py` |
| No dependency or migration drift | `test_identity_assertion_replay_no_dependency_or_migration.py` |
| Performance smoke | `test_identity_assertion_replay_performance.py` |
