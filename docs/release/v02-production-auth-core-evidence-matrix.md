# v0.2 Production Auth Core Evidence Matrix

| Evidence | Path | Status |
| --- | --- | --- |
| Contracts | `services/brain-api/src/aion_brain/contracts/production_auth.py` | implemented_disabled |
| Core service | `services/brain-api/src/aion_brain/production_auth/core.py` | implemented_disabled |
| Config mapping | `services/brain-api/src/aion_brain/production_auth/config.py` | fail_closed |
| Policy | `services/brain-api/src/aion_brain/production_auth/policy.py` | blocked |
| Audit | `services/brain-api/src/aion_brain/production_auth/audit.py` | redacted |
| Provenance | `services/brain-api/src/aion_brain/production_auth/provenance.py` | redacted |
| Diagnostics | `services/brain-api/src/aion_brain/production_auth/diagnostics.py` | redacted |
| Static evidence | `operator-console-static/demo-data/production-auth-core-status.json` | read_only |
| Runtime hold | `operator-console-static/demo-data/production-auth-runtime-hold.json` | held |

All evidence references `authorization_transaction_id=AION-151-PA-0001`,
`authorization_consumed_by_task=AION-152`, and
`authorization_reusable=false`.
