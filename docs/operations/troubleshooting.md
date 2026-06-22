# AION v0.1 Troubleshooting

Use this table for local release-candidate failures. Fix the underlying local
condition; do not bypass gates or enable disabled features.

| Symptom | Likely cause | Exact check command | Safe fix | Unsafe fix to avoid |
| --- | --- | --- | --- | --- |
| Docker service not starting | Invalid compose config or stale local container | `docker compose config --quiet && docker compose ps` | Rebuild the local stack and inspect service logs. | Editing compose to skip required services. |
| Health endpoint failing | Brain API is not booted or wrong port is used | `curl -fsS http://localhost:8080/health` | Check `docker compose logs brain-api`. | Claiming release readiness without health. |
| Readiness dependency unavailable | Postgres, Redis, NATS, or OPA is unavailable | `curl -fsS http://localhost:8080/health/ready` | Restart the named dependency. | Disabling readiness checks. |
| OPA policy unknown action | Policy vocabulary missing an action | `./scripts/policy-coverage.sh` | Add generic policy coverage and rerun. | Broad allow rules. |
| 403 from local smoke | Policy context or OPA bridge mismatch | `docker compose logs opa` | Restart OPA and verify the action family. | Bypassing policy. |
| SDK venv missing typer | SDK tests are running in the wrong venv | `packages/aion-sdk-python/.venv/bin/python -m pytest packages/aion-sdk-python/tests -q` | Use the SDK venv. | Installing packages globally. |
| Brain venv import mismatch | Brain tests are running in the wrong venv | `services/brain-api/.venv/bin/python -m pytest services/brain-api/tests -q` | Use the Brain venv. | Editing imports to match a system Python path. |
| Postgres migration mismatch | Migration files or local DB schema drifted | `./scripts/migration-check.sh` | Recreate local dev data only when acceptable. | Manual production-style DB edits. |
| Redis/NATS unavailable | Local service is down or port is occupied | `docker compose ps redis nats` | Restart the service or free the port. | Removing Redis or NATS from compose. |
| Golden path warning | Synthetic scenario produced a warning | `./scripts/golden-path.sh --offline-ok` | Inspect the golden path report. | Marking warnings as pass without review. |
| RC gate missing required check | Script or matrix did not supply a required check | `./scripts/rc-check.sh --offline-ok` | Add or rerun the missing local check. | Lowering the matrix threshold. |
| Freeze gate blocked | Freeze prerequisite failed | `./scripts/aionctl.sh --scope workspace:main freeze run --version 0.1.0` | Fix the named freeze check. | Freezing with an unresolved blocker. |
| Release package dry-run failed | Handoff or package metadata is incomplete | `./scripts/package-release.sh --dry-run` | Fix package metadata and rerun dry-run. | Publishing a package manually. |
| No-domain-drift failure | Domain terms entered Brain core or examples | `./scripts/verify-no-domain-drift.sh` | Remove vertical workflow logic. | Adding exceptions for demos. |
| Boundary check failure | Vendor or infra object leaked through Brain public API | `./scripts/boundary-check.sh` | Move implementation behind an adapter. | Exposing raw client objects. |
| Typecheck failure | Contract or literal typing drifted | `./scripts/typecheck.sh` | Tighten public types and rerun. | Adding broad `Any` at public boundaries. |
| Ruff failure | Formatting or lint drift | `./scripts/lint.sh` | Run format and fix lint. | Ignoring lint for release. |
| OpenAPI hygiene failure | API schema drifted | `./scripts/openapi-hygiene.sh` | Fix route or contract shape. | Hiding endpoints from schema. |
| Policy coverage failure | Policy catalog and OPA coverage diverged | `./scripts/policy-coverage.sh` | Add missing generic action coverage. | Wildcard allow. |
| Extension intake blocked | Manifest requests unsafe behavior or policy denies it | `./scripts/aionctl.sh --scope workspace:main extensions validate --manifest-file examples/demo/generic-extension-manifest.json` | Keep manifest metadata-only. | Enabling code loading. |
| Module binding validation blocked | Binding references missing contracts or unsafe flags | `./scripts/aionctl.sh --scope workspace:main module-bindings validate --dry-run` | Fix metadata and rerun dry-run. | Activating the binding. |
| Conformance readiness blocked | Required schema or readiness checks are missing | `./scripts/aionctl.sh --scope workspace:main readiness assess --capability-binding-id <capability-binding-id>` | Create required metadata and rerun. | Treating readiness as activation. |
