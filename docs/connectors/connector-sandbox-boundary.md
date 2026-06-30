# Connector Sandbox Boundary

AION-112 defines the connector sandbox as a design and readiness boundary only.
It does not add a real sandbox runtime, execute connector code, grant file
access, grant network access, store credentials, store tokens, spawn processes,
perform dynamic imports, install packages, activate connectors, or register
runtime routes.

The boundary evidence is exposed through read-only contracts, API responses,
SDK helpers, CLI preview commands, JSON examples, static console demo data,
kernel diagnostics, release packaging, freeze checks, and hardening checks.

Boundary flags that must stay false:

- `filesystem_access_allowed`
- `network_access_allowed`
- `credential_access_allowed`
- `token_access_allowed`
- `process_spawn_allowed`
- `dynamic_import_allowed`
- `package_install_allowed`
- `runtime_execution_allowed`
- `connector_activation_allowed`

Audit and provenance remain required for any readiness preview. A future
milestone may replace this design boundary only by adding a new release gate,
new threat model evidence, new no-go regression coverage, and explicit
operator approval requirements.
