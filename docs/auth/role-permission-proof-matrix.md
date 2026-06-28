# Role Permission Proof Matrix

AION-096 defines a local role matrix for the read-only Operator Console. The roles are `viewer`, `operator`, `reviewer`, `admin`, `auditor`, and `system_service`.

The static console exposes only `viewer`, `operator`, `reviewer`, `admin`, and `auditor`. `system_service` is internal and is not a UI role.

Every matrix decision keeps these flags false: `write_allowed`, `execute_allowed`, `activation_allowed`, and `external_calls_allowed`. Forbidden actions stay visible as descriptors so the console can prove what remains blocked.

The matrix is available through the local-auth service and SDK as read-only data. It is not login, not session persistence, and not production authorization.
