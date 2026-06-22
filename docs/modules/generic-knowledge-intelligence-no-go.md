# Generic Knowledge Intelligence No-Go Conditions

The Generic Knowledge Intelligence module pack must remain metadata-only. Stop
review and reject the package if any no-go condition is present.

## No-Go Conditions

- executable payload present
- external dependency declared
- source URL present
- dynamic route requested
- capability activation requested
- runtime registration requested
- full autonomy requested
- raw secret access requested
- external model calls requested
- tool execution requested
- domain workflow included
- `activation_ready=true` in v0.1
- code loading enabled

## Required Response

When a no-go condition appears:

1. Stop the demo.
2. Do not run optional API-backed dry-run steps.
3. Do not create activation records.
4. Do not create runtime registration previews.
5. Record the failing fixture or document path.
6. Keep the v0.1 release baseline unchanged.

## Expected v0.1 Result

The correct v0.1 result is a readable readiness trail with activation blocked.
Any path that produces active runtime behavior is outside AION-084.
