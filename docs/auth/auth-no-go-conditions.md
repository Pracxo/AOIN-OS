# Auth No-Go Conditions

The following conditions block auth implementation or release:

- password storage added without design,
- external identity provider added without threat model,
- login endpoint added without policy integration,
- session token stored insecurely,
- console writes enabled without role model,
- raw prompt visible,
- secret visible,
- hidden reasoning visible,
- activation control exposed,
- provider enablement exposed,
- policy bypass possible,
- audit missing.

AION-093 is explicitly design-only. If any no-go condition appears in a later
implementation, the work must stop until the control is redesigned and gated.

## AION-098 Production Auth No-Go Conditions

AION-098 is architecture-only. It blocks runtime work if any task adds provider
SDKs, login/logout routes, credentials, tokens, cookies, session persistence,
provider calls, migrations, frontend package files, production auth enablement,
ActorContext bypass, policy bypass, audit bypass, or dry-run action
authorization bypass.
