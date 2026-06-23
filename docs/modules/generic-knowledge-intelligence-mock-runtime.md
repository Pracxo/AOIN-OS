# Generic Knowledge Intelligence Mock Runtime Trail

Generic Knowledge Intelligence now includes deterministic module mock runtime
fixtures under `examples/modules/generic-knowledge-intelligence/`.

The trail adds:

- `mock-profile.json`
- `mock-invocation-request.json`
- `mock-output-example.json`
- `mock-readiness-trail.json`

These fixtures complete the metadata-only demo path:

`manifest -> intake -> slot -> binding -> mock profile -> mock invocation -> synthetic output -> conformance -> readiness -> activation blocker`

The mock runtime evidence remains synthetic and dry-run only. It does not
execute the Generic Knowledge package, load code, install dependencies, call
external services, register routes, mutate runtime configuration, activate a
module, or implement domain-specific logic.

The local demo script validates the fixtures offline with:

```bash
./scripts/generic-knowledge-demo.sh --offline-ok --skip-api
```

When a local Brain API is available and `--skip-api` is not set, the script can
also create the module slot, capability bindings, mock profile, and mock
invocation records through local API calls.
