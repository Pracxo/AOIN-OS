# v0.2 Actor Context Trust Boundary Evidence Matrix

| Evidence | Owner | Gate | State | Notes |
| --- | --- | --- | --- | --- |
| AION-159 authorization | security reviewer | `v02-actor-context-trust-boundary-authorization-check.sh` | active until AION-160 merge | `AION-159-PA-0005` scopes the remediation. |
| Fail-closed resolver | platform reviewer | `production-auth-actor-context-trust-boundary-check.sh` | implemented | Resolver receives structured input, not raw HTTP requests. |
| Development simulation isolation | local development reviewer | focused pytest | implemented | Identity headers accepted only for `env=development` and `dev_auth_enabled=true`. |
| RequestIdentityContext precedence | auth boundary reviewer | focused pytest | implemented | Disabled identity context keeps actor context anonymous. |
| RequestContext correlation | API boundary reviewer | focused pytest | implemented | Only trace and correlation project to ActorContext. |
| Privilege escalation regression | security reviewer | focused pytest | implemented | Hostile actor, workspace, role, permission, and scope headers ignored. |
| Runtime hold | release reviewer | `production-auth-actor-context-trust-boundary-runtime-hold.sh` | held | No runtime auth, routes, providers, protected material, packages, migrations, tags, or releases. |

## AION-161 Closeout Evidence

| Evidence | State | Notes |
| --- | --- | --- |
| AION-159 lifecycle | historical | Consumed by AION-160 PR 70 and merge commit `bfc2afdc96358559027ee36efc0bc26ed3bb796d`. |
| AION-160 remediation | implemented | Fail-closed ActorContext resolution is merged. |
| AION-161 authorization | active | `AION-161-PA-0006` authorizes AION-162 offline Ed25519 verification only. |
