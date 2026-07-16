# v0.2 Production Auth Request Identity Boundary No-Go

`AION-156` remains a disabled implementation. The no-go regression gate rejects
new public production-auth or request-identity routers, login/logout/callback
or token routes, OpenAPI security schemes, package files, lockfiles, migrations,
SDK runtime resources, CLI runtime commands, network imports, provider SDK
runtime surfaces, header/cookie/body/query access in request identity source,
runtime guard release, v0.2 tags, and v0.2 releases.

Allowed implementation-presence evidence is exact-path scoped to AION-156 files
and does not enable runtime authentication.
