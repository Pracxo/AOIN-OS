# v0.2 Production Auth Authorization Evidence Matrix

| Authorization area | Evidence source | Required reviewer | Required ADR | Required gate | Authorization state | Runtime state | Blocker | Expiry | Revocation | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Scoped transaction | explicit approval record | security reviewer | ADR 0142 | authorization check | approved for production-auth-core | runtime disabled | second approval | AION-152 merge | revoke AION-151-PA-0001 | exact scope only |
| Implementation scope | implementation scope doc | platform reviewer | ADR 0142 | no-go regression | disabled core only | runtime disabled | scope expansion | AION-152 merge | revoke AION-151-PA-0001 | no endpoint work |
| Runtime guard hold | runtime guard hold doc | runtime governance reviewer | ADR 0142 | runtime guard hold | guard hold active | no-go true | guard release | AION-152 merge | revoke AION-151-PA-0001 | no runtime release |
| Static evidence | demo-data JSON | audit reviewer | ADR 0142 | docs check | read-only evidence | runtime disabled | unsafe content | AION-152 merge | revoke AION-151-PA-0001 | synthetic only |
| Release boundary | checklist | release reviewer | ADR 0142 | final docs audit | no release approval | no tag | v0.2 tag or release | AION-152 merge | revoke AION-151-PA-0001 | release remains blocked |
