# Connector Sandbox Design

The connector sandbox remains design-only. AION-113 does not change sandbox
execution, filesystem, network, process, dynamic import, package install,
activation, credential, or token permissions.

The connector credential boundary is separate from sandbox design and keeps
credential storage, token storage, secret material, and runtime credential
access disabled.
## AION-114 Release Gate Input

The connector sandbox design is a release-gate input only. AION-114 keeps real
sandbox execution, filesystem access, network access, process spawning, dynamic
imports, package installation, and activation disabled.
