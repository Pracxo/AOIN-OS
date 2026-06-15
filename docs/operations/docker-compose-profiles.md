# Docker Compose Profiles

## Default Core

The default core stack starts:

- `brain-api`
- `postgres`
- `redis`
- `nats`
- `opa`

## Optional Profiles

- `storage`: local object storage placeholder services.
- `workflow`: durable workflow backend placeholder services.
- `observability`: local telemetry collector placeholder services.
- `model-gateway`: model gateway placeholder services.
- `graph-memory`: reserved for future graph memory services.
- `mcp`: MCP compatibility placeholder services.

Optional profiles are disabled by default. External calls are disabled unless
explicitly configured. Do not place secrets in compose files.

Future profiles must preserve adapter boundaries and remain off by default.
