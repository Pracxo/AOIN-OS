# v0.2 Offline Identity Assertion Verification No-Go

AION-162 remains no-go for runtime authentication.

The following remain prohibited:

- request authentication
- ActorContext application
- RequestIdentityContext application
- HTTP header, cookie, or body parsing
- runtime signing services
- runtime private signing material
- provider discovery
- JWKS network fetch
- external calls
- raw assertion logging
- verified-claim persistence
- replay caches
- API routes
- OpenAPI security schemes
- package manifests beyond the existing brain-api pyproject dependency line
- lockfiles
- migrations
- SDK or CLI runtime surfaces
- connector runtime
- operator writes
- module activation
- sandbox execution
- runtime guard release
- v0.2 tags or releases
