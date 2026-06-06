# AOIN OS Exchange

This folder is the implementation instruction exchange for AOIN OS.

Use `implementation-queue.md` to add new instructions. Put the newest request under `Queued`, using the next task number.

Codex will treat this queue as the source of implementation work when you ask it to process queued instructions.

## Status Flow

- `Queued`: waiting to be picked up.
- `In Progress`: currently being actioned.
- `Done`: completed and verified.
- `Blocked`: needs your input before work can continue.

## Task Format

```md
### TASK-0001 - Short title
Status: Queued
Priority: Normal
Created: YYYY-MM-DD HH:MM

Instruction:
Your implementation instruction here.

Acceptance:
- What must be true when complete.
```
