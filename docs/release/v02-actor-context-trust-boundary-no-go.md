# v0.2 Actor Context Trust Boundary No-Go

AION-159 rejects:

- AION-157 reactivation
- a second active authorization
- unknown approved authorization records
- AION-159 scope widening
- wrong AION-160 task, candidate, workstream, parent, or scope
- implementation-source changes in AION-159
- production identity-header trust
- production role-header trust
- production permission-header trust
- production security-scope header trust
- runtime authentication
- Authorization or Cookie parsing
- protected material handling
- providers or external calls
- auth endpoints
- OpenAPI security
- packages or lockfiles
- migrations
- SDK or CLI runtime surfaces
- connector runtime
- operator writes
- module activation
- sandbox execution
- v0.2 tags or releases

The no-go state remains active until AION-160 lands and its own guards pass.
