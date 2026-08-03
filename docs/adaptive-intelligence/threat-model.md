# Adaptive Intelligence Threat Model

AION-245 records the threat model for the AION-246 foundation.

Threat scenarios include provider lock-in, unapproved live provider calls, public network egress, DNS lookup, credential value exposure, token persistence, authorization-header creation, raw prompt or response retention, hidden-reasoning capture, model-output-triggered execution, prompt injection, unverified evidence promotion, memory writes, belief mutation, engagement learning without evaluation, real connector execution, real tool execution, background scheduling, source mutation, Git mutation, automatic merge, production deployment, and model-weight training.

Mitigations are provider-neutral contracts, deterministic fixtures, explicit budgets, circuit breakers, redaction, fingerprints, replay rejection, audit evidence, operator review records, static console evidence, no-network controls, no-credential controls, no-memory-write controls, no-tool controls, and release/runtime holds.
