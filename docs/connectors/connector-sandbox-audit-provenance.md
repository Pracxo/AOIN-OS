# Connector Sandbox Audit and Provenance

Connector sandbox readiness previews record audit metadata and carry
provenance identifiers so the operator can verify that a sandbox request stayed
inside the design boundary.

Recorded evidence includes:

- readiness identifier
- trace identifier when present
- actor identifier when present
- owner scope
- readiness status
- false runtime, filesystem, network, credential, token, process, import,
  package install, and activation flags

The audit helper is best effort and local. It does not persist credentials,
tokens, request bodies, external endpoints, connector payloads, or provider
objects.
