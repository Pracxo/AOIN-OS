# Connector Release Evidence Matrix

| Area | Gate script | Required evidence | Expected safe value | Release blocker if failed | Notes |
| --- | --- | --- | --- | --- | --- |
| runtime disabled | `connector-runtime-review.sh` | runtime status and disabled proof | `connector_runtime_enabled=false` | yes | no runtime execution |
| external calls | `connector-runtime-no-external-call-regression.sh` | no external call evidence pack | `external_calls_enabled=false` | yes | no network clients |
| simulator | `connector-simulator-check.sh` | synthetic simulator preview | `synthetic=true` | yes | dry-run only |
| simulator no-go | `connector-simulator-no-go-regression.sh` | no execution paths | `connector_activation_enabled=false` | yes | no route registration |
| policy catalog | `connector-policy-check.sh` | action catalog and denial rules | `implementation_approved=false` | yes | deny runtime allow paths |
| policy no-go | `connector-policy-no-go-regression.sh` | policy no-go result | runtime allow absent | yes | no bypass |
| sandbox boundary | `connector-sandbox-check.sh` | sandbox status/readiness | `sandbox_execution_enabled=false` | yes | no filesystem/network/process/import/install |
| sandbox no-go | `connector-sandbox-no-go-regression.sh` | denied capabilities | all runtime capabilities denied | yes | design-only |
| credential boundary | `connector-credential-check.sh` | credential architecture | `credentials_present=false` | yes | no storage material |
| credential no-go | `connector-credential-no-go-regression.sh` | credential no-go result | `token_storage_enabled=false` | yes | no OAuth/OIDC/SAML runtime |
| static console | `operator-console-static-check.sh` | bundled JSON panels | `read_only=true` | yes | no inputs or buttons |
| docs | `docs-check.sh` | docs and JSON examples | valid docs/examples | yes | ADR indexed |
| domain boundary | `verify-no-domain-drift.sh` | domain drift scan | no drift | yes | no domain module logic |
| architecture boundary | `boundary-check.sh` | vendor/domain boundary tests | passed | yes | no external vendor leakage |
| release gate | `connector-release-gate.sh` | consolidated release result | passed | yes | AION-114 gate |
| safety freeze | `connector-safety-freeze.sh` | tag and release freeze result | passed | yes | v0.1 tag untouched |
