# Local Session Boundary

The local session boundary exists to keep console session semantics separate
from production authentication.

Required invariants:

- `read_only=true`
- `dev_only=true`
- `production_session=false`
- `credential_backed=false`
- `token_issued=false`
- `cookie_issued=false`
- `persistent=false`
- `write_allowed=false`
- `execute_allowed=false`
- `activation_allowed=false`
- `external_calls_allowed=false`

The boundary check fails if any preview grants write, execution, activation,
external call, credential-backed, token-backed, cookie-backed, persistent, or
production-session behavior.

No AION-095 database migration exists. If persistence becomes necessary later,
the work must stop for explicit architecture approval.
