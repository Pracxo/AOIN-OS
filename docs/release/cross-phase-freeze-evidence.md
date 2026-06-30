# Cross-Phase Freeze Evidence

## Purpose

This document records the cross-phase evidence required for the AION-118
post-v0.1 release candidate gate. It freezes the current post-v0.1 platform
state as evidence only and keeps all future runtime implementation unapproved.

## Evidence Matrix

| Phase | Required evidence | Gate | Frozen assertion |
| --- | --- | --- | --- |
| Operator platform regression | Operator checkpoint, static console safety, role filtering, dry-run action authorization, local auth and session previews | `./scripts/operator-platform-regression.sh` | Read-only operator console, no write execution |
| Operator platform freeze gate | Freeze evidence, stabilization runbook, release blockers | `./scripts/operator-platform-freeze-gate.sh` | Operator platform remains frozen before implementation |
| Connector platform regression | Connector checkpoint, release gate, safety freeze, runtime review, simulator, policy, sandbox, credential evidence | `./scripts/connector-platform-regression.sh` | Connector implementation remains unapproved |
| Connector platform stabilization gate | Connector phase freeze, long-running regression matrix, safety baseline lock | `./scripts/connector-platform-stabilization-gate.sh` | Connector phase remains frozen after checkpoint |
| Platform integration checkpoint | Operator and connector integration evidence, approval state summary, closeout checklist | `./scripts/platform-integration-checkpoint.sh` | Cross-phase checkpoint passes without runtime approval |
| Platform integration freeze | Full integration freeze, tag ancestry evidence, nested gate guard | `./scripts/platform-integration-freeze-check.sh` | `aion-v0.1.0` remains untouched and future runtime stays frozen |
| Auth prototype review | Disabled auth runtime, mock claims, local auth safety evidence | `./scripts/auth-prototype-review.sh` | Production auth is not approved and no credentials or tokens are stored |
| Module activation design review | Plugin boundary pack, code loading proof, runtime registration proof, capability activation proof | `./scripts/module-activation-design-review.sh` | Module activation remains design-only and disabled |
| Static console safety | Dependency-free static UI, safe command-copy allowlist, no input or execution controls | `./scripts/static-console-safety-check.sh` | Static console remains read-only and local |
| Docs and boundary checks | Docs check, final docs audit, domain drift check, boundary check | `./scripts/docs-check.sh`, `./scripts/final-docs-audit.sh`, `./scripts/verify-no-domain-drift.sh`, `./scripts/boundary-check.sh` | Brain remains documented, domain-neutral, and boundary-owned |

## Frozen Values

The evidence is valid only while these values stay false:

- `operator_write_execution_approved=false`
- `connector_implementation_approved=false`
- `production_auth_approved=false`
- `module_activation_approved=false`
- `external_calls_approved=false`
- `credential_storage_approved=false`
- `token_storage_approved=false`
- `sandbox_execution_approved=false`
- `v02_release_approved=false`
- `v02_tag_created=false`

## Interpretation

The freeze evidence is a release candidate baseline, not a runtime approval.
Future v0.2 work may use this baseline for planning, but any implementation
requires new ADRs, explicit gates, and a narrowed scope.
