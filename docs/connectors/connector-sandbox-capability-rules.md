# Connector Sandbox Capability Rules

AION-112 adds connector sandbox capability rules so future work has a
deterministic allow and deny shape before implementation begins.

Allowed preview rule:

- `connector.sandbox.readiness.preview`

Denied future capability rules:

- `connector.sandbox.filesystem.read`
- `connector.sandbox.filesystem.write`
- `connector.sandbox.network.egress`
- `connector.sandbox.network.ingress`
- `connector.sandbox.credentials.read`
- `connector.sandbox.tokens.read`
- `connector.sandbox.process.spawn`
- `connector.sandbox.dynamic_import`
- `connector.sandbox.package_install`
- `connector.sandbox.runtime.execute`
- `connector.sandbox.activate`

Denied rules are visible so operators can inspect blockers before future
implementation work. They do not grant dry-run execution, runtime execution,
network access, credential access, token access, process spawning, package
installation, dynamic imports, or activation.
