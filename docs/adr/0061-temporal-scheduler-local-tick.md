# 0061: Temporal Scheduler, Reminder Queue, Due Item Ledger, and Local Tick Orchestrator

## Status

Accepted.

## Decision

AION Brain adds a Temporal Scheduler, Reminder Queue, Due Item Ledger, and Local Tick Orchestrator.

The scheduler is local and tick-driven in v0.1. It does not start a background worker. Schedules create scheduler-owned due items, reminders, local notifications, operator items, or action proposals only when explicitly configured and when an explicit tick request allows those records.

Schedules do not execute target actions. Due items do not execute target actions. Reminders do not send external messages. Tick runs do not run commands, workflows, backups, security checks, release gates, freeze gates, resilience tests, or external scheduler integrations.

## Reason

AION needs time-based coordination without introducing uncontrolled background execution. A local tick layer gives operators and future UI surfaces a deterministic way to inspect schedules, due items, reminders, missed schedules, and scheduler reports.

## Consequence

Future UI, operator workflows, and governed adapters can call tick or inspect due items. Future external scheduler adapters can be introduced behind governed contracts without changing the core Brain scheduler contract.

## Constraints

- No background worker in v0.1.
- No external calendars.
- No automatic execution.
- No external delivery.
- No domain-specific scheduling.
- Scheduler records remain Brain-owned and frontend-agnostic.
