# Development Identity Simulation

AION-160 preserves local development identity simulation, but only behind the
exact shared gate:

```python
settings.env == "development" and settings.dev_auth_enabled is True
```

No other environment value enables synthetic identity headers. Production,
staging, test, CI, local, empty, and disabled-dev-auth configurations ignore
identity-bearing `X-AION` headers.

Inside the exact development gate only, these headers may provide synthetic
local values:

- `X-AION-Actor-ID`
- `X-AION-Workspace-ID`
- `X-AION-Roles`
- `X-AION-Permissions`
- `X-AION-Security-Scope`

Development simulation is not production authentication. It does not parse
Authorization headers, cookies, credentials, passwords, tokens, sessions,
provider payloads, or protected material. It does not contact external
providers and does not create authenticated requests.

When a valid `RequestContext` is present, its trace and correlation values take
precedence for actor-context correlation. Only when the request context is
absent and the exact development gate is active does the compatibility path
preserve the legacy development trace and correlation header fallback.
