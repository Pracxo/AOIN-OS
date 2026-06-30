# Connector Sandbox Design

The connector sandbox remains design-only. AION-113 does not change sandbox
execution, filesystem, network, process, dynamic import, package install,
activation, credential, or token permissions.

The connector credential boundary is separate from sandbox design and keeps
credential storage, token storage, secret material, and runtime credential
access disabled.
