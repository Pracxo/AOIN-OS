# Connector Credential Store Architecture

AION-113 defines the future connector credential store architecture as a design boundary only. No credential store exists in this milestone, no token store exists, and no connector runtime is allowed to request credential material.

The architecture is represented by `ConnectorCredentialBoundary`. The boundary requires rotation, revocation, audit, and provenance before any future storage work can begin. The disabled flags are part of the contract: `credential_storage_enabled=false`, `token_storage_enabled=false`, `secret_material_present=false`, `external_identity_runtime_enabled=false`, and `connector_runtime_credential_access_enabled=false`.

Future implementation prerequisites:

- production auth architecture must be implemented and reviewed
- a dedicated secret-store backend must be selected
- key-management ownership must be documented
- rotation and revocation workflows must be tested
- audit and provenance records must be tamper-evident
- connector runtime credential access must pass a separate release gate

This document is not an implementation plan for storing material. It is a no-go boundary for later design review.

## AION-114 Release Gate Input

The credential architecture is required release evidence for AION-114. The
release gate keeps credential storage, token storage, raw material persistence,
external identity runtime, and connector runtime credential access disabled.
