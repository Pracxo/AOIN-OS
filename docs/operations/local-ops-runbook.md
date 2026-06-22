# Local Ops Runbook

## Prerequisites

- Docker Desktop
- Python 3.12
- Git

## First Run

1. Clone the repository.
2. Copy `.env.example` to `.env` for local-only values.
3. Start the core stack:

```bash
scripts/docker-up-core.sh
```

4. Check health:

```bash
curl http://localhost:8080/health
curl http://localhost:8080/health/ready
```

5. Run the kernel self-test:

```bash
scripts/kernel-self-test.sh
```

6. Run the SDK smoke test:

```bash
scripts/aionctl.sh health
```

7. Seed and run the default scenario pack:

```bash
scripts/aionctl.sh scenarios seed-defaults
scripts/aionctl.sh scenarios run --scenario-id golden_path_brain
```

8. Run the deterministic release baseline:

```bash
scripts/aionctl.sh release-baseline run --version 0.1.0
```

9. Stop the stack:

```bash
scripts/docker-down.sh
```

## Ports

- Brain API: `8080`
- Postgres: `5432`
- Redis: `6379`
- NATS: `4222`, monitoring on `8222`
- OPA: `8181`

## Notes

The default stack is core-only. Optional profiles are disabled by default. Do
not add secrets to compose files; use local environment values only.

Common failure modes are covered in `docs/operations/troubleshooting.md`.
