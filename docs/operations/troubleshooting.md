# Troubleshooting

## Brain API Does Not Start

Run `docker compose logs brain-api` and confirm `.env.example` or `.env` is
available. Rebuild with `scripts/docker-build.sh`.

## Postgres Unavailable

Check `docker compose ps postgres` and confirm port `5432` is free. Recreate
local volumes only when local data can be discarded.

## Redis Unavailable

Check `docker compose ps redis` and confirm port `6379` is free.

## NATS Unavailable

Check `docker compose ps nats` and confirm JetStream config is mounted from
`infra/nats/nats.conf`.

## OPA Unavailable

Check `docker compose ps opa` and confirm `infra/opa/policies` is mounted.
Policy failures must fail closed.

## Health Ready Degraded

`/health/ready` reports each dependency status. Use the failing check name to
inspect the matching compose service.

## Migrations Failed

Run `scripts/migration-check.sh` first. Inspect the latest file in
`infra/postgres/migrations` for duplicate tables or destructive operations.

## SDK Cannot Connect

Confirm `AION_BASE_URL` or the CLI `--base-url` points to
`http://localhost:8080`.

## Docker Build Failed

Run `docker compose config` and then `scripts/docker-build.sh`. Rebuild after
dependency changes.

## Policy Denied Request

Inspect the returned policy reason and constraints. Run
`scripts/policy-coverage.sh` to verify catalog coverage.

## Autonomy Blocked Request

Autonomy defaults are bounded. Check the active run level and approval
requirements before retrying.

## Boundary Check Failed

Run `scripts/boundary-check.sh`. Fix direct vendor leakage, forbidden source
directories, or raw infrastructure access outside adapter boundaries.
