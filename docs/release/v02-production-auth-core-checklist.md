# v0.2 Production Auth Core Checklist

- [x] AION-151 authorization is referenced.
- [x] `authorization_transaction_id=AION-151-PA-0001`.
- [x] `authorization_scope=disabled-production-auth-core`.
- [x] `authorization_consumed_by_task=AION-152`.
- [x] `authorization_reusable=false`.
- [x] Internal package is separate from `aion_brain.auth_runtime`.
- [x] Contracts use strict Pydantic models.
- [x] Config fails closed if runtime flags are true.
- [x] Policy decisions are blocked or denied only.
- [x] Audit and provenance are redacted.
- [x] Kernel diagnostics expose safe status only.
- [x] Static evidence is bundled JSON only.
- [x] Public production-auth API routes are absent.
- [x] Packages, migrations, tags, and releases are absent.
