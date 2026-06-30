# Connector Sandbox No-Go Conditions

AION-112 must fail closed if any connector sandbox artifact introduces a
runtime path.

No-go conditions:

- Real sandbox execution is added.
- Filesystem access is added.
- Network access is added.
- Credential or token access is added.
- Process spawning is added.
- Dynamic import behavior is added.
- Package installation behavior is added.
- Connector activation or runtime route registration is added.
- A connector or provider SDK dependency is added.
- A static console control can enable, run, execute, connect, call, install,
  or activate connector sandbox behavior.

The `connector-sandbox-no-go-regression.sh` script scans source, examples,
static demo data, and docs for these conditions. The check is intentionally
separate from the older connector runtime review checks so the sandbox design
boundary can evolve without weakening previous blockers.
