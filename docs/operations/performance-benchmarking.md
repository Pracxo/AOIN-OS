# Performance Benchmarking

AION v0.1 benchmarks are local, deterministic, and side-effect-safe. They do
not perform cloud load testing or call external providers.

The performance layer measures generic Brain operations and stores local timing
samples. It is a measurement harness, not production monitoring and not an
optimization task.

## Default Suites

- `smoke`: health, kernel status, and no-op timing.
- `api_latency`: local API-style latency checks.
- `memory`: generic memory create and retrieve paths.
- `retrieval`: retrieval query and context compilation.
- `reasoning`: deterministic reasoning, planning, and Brain think.
- `visual`: Brain Map projection timing.
- `full_local`: broad local dry-run suite across Brain subsystems.

## Capacity Baseline

A capacity baseline is created from one or more benchmark runs. It records
per-operation p50, p95, p99, max latency, sample counts, error counts, and local
environment metadata. It contains no secrets and does not require optional
adapters.

## Regression Checks

Regression comparison checks p95 and max latency by operation. A p95 regression
above 25 percent fails. A p95 regression from 10 to 25 percent warns. A p95
improvement above 10 percent is reported as an improvement.

## Resource Budgets

Resource budget profiles define generic thresholds such as request duration,
Brain think duration, retrieval duration, visual map duration, and record
counts. v0.1 defaults to `report_only`; warn and block modes are contract
values for future wiring.

## CLI

```bash
./scripts/aionctl.sh --scope workspace:main performance benchmarks seed-defaults
./scripts/aionctl.sh --scope workspace:main performance run
./scripts/aionctl.sh --scope workspace:main performance baselines create --run-id <benchmark_run_id>
./scripts/aionctl.sh --scope workspace:main performance summary
```

## Scripts

```bash
./scripts/benchmark-local.sh
./scripts/capacity-baseline.sh
```

Both scripts require a running local Brain API. If the server is unavailable,
they print a clear message and exit.

## Known Limits

- No cloud load testing in v0.1.
- No provider calls.
- No production monitoring.
- No background worker requirement.
- No request or response bodies are stored in performance samples.
- No domain-specific benchmark suites belong in Brain core.
