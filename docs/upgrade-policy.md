# AION Upgrade Policy

AION v0.1 treats public Brain contracts as the compatibility boundary. Future
upgrades must preserve domain-neutral contracts or ship an explicit migration
baseline and deprecation path.

## Rules

- Public AION contracts must remain provider-neutral.
- Database migrations must be additive by default.
- Destructive migrations require explicit review and a migration-level override.
- Optional adapters remain optional and must not become startup requirements.
- SDK resources must call public HTTP paths and must not import server internals.
- Freeze gates must run locally without Docker services by default in tests.
- Full autonomy remains disabled by default.

## Compatibility

The compatibility matrix records API, SDK, Python, local service, and optional
adapter status. Optional adapters may report warnings when unavailable, but
they must not make the core release incompatible.

## Migrations

The migration baseline hashes migration files, records table inventory, and
flags destructive operations in upgrade paths. Downgrade-only destructive
operations do not fail the baseline.
