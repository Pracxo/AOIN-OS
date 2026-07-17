# v0.2 Actor Context Trust Boundary No-Go

AION-160 fails closed if any remediation work introduces production identity
trust or runtime authentication behavior.

No-go conditions:

- non-development identity-bearing `X-AION` headers populate `ActorContext`
- a loose environment alias enables development simulation
- `RequestContext.actor_id` or `RequestContext.workspace_id` populates `ActorContext`
- `RequestIdentityContext` is treated as authenticated identity
- Authorization, Cookie, credential, password, token, session, provider, or network behavior is added
- auth API routers, OpenAPI security, SDK runtime resources, CLI runtime commands, package files, lockfiles, or migrations are added
- connector runtime, operator writes, module activation, sandbox execution, runtime guard release, `v0.2` tags, or `v0.2` releases are added

The no-go gate is:

```sh
./scripts/production-auth-actor-context-trust-boundary-no-go-regression.sh
```
