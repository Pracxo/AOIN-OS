# v0.2 Production Auth Authorization No-Go

The AION-151 authorization is blocked by any of the following:

- any second approved authorization transaction
- any approved candidate other than `production-auth-core`
- any authorization scope broader than `disabled-production-auth-core`
- runtime enablement true
- runtime guard release true
- login, logout, or callback endpoint approval true
- credential, password, token, session, or cookie storage approval true
- provider or external-call approval true
- migration, package, or lockfile approval true
- connector, operator, module, or sandbox enablement true
- v0.2 tag or release creation

The only allowed true approval fields are inside the canonical
`AION-151-PA-0001` record. They authorize future AION-152 implementation work
only and have no runtime effect.
