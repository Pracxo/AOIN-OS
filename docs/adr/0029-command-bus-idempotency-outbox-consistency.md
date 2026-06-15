# ADR 0029: Command Bus, Idempotency, Outbox, and Consistency Guard

## Decision

AION Brain v0.1 adds a Command Bus and Idempotency Service. Brain operations
can be recorded as generic command records, checked for duplicate request
effects, gated through policy/autonomy/risk/approval, and dispatched through
safe local handlers.

AION Brain v0.1 also adds a Transactional Outbox and Inbox Deduplication.
Outbox messages are persisted locally and processed manually. Inbox messages
record source and external message IDs so duplicate deliveries can be
suppressed.

No background processors start automatically in v0.1.

## Reason

AION needs retry-safe and duplicate-safe Brain operations before future modules,
brokers, runtimes, or external execution layers are added. Event reaction and
workflow reliability must not depend on HTTP, NATS, or module runtime
at-most-once behavior.

## Consequences

Event reaction, workflows, execution, cognitive cycles, and future modules can
move toward reliable local consistency without relying on broker guarantees.
The consistency state is owned by AION contracts and can later be transported
through external queues without changing public Brain semantics.

## Constraints

The v0.1 command consistency layer has no domain-specific command logic, no
external side effects by default, no shell execution, and no automatically
started background processors.
