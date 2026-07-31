# Capability Runtime Idempotency

AION-235 idempotency is session-scoped. Exact replay returns the existing safe result without a second execution. Changed replay with the same request ID is rejected. Cross-session replay, capability substitution, connector substitution, input substitution, plan substitution and output-schema substitution fail closed.
