# Instruction Hierarchy and Preference Ledger

AION Brain owns instruction resolution. External clients may submit
instructions, preferences, constraints, and style profiles, but they do not
own precedence and cannot expand permissions.

Precedence:

1. AION policy and hard safety constraints
2. Runtime configuration constraints
3. Autonomy mode constraints
4. Risk and approval constraints
5. Capability availability and sandbox constraints
6. Explicit current-session instructions
7. Task or workflow instructions
8. Workspace instructions
9. Confirmed actor preferences
10. Learned preference candidates

Preferences shape response and context only. They do not override policy,
autonomy, approvals, runtime configuration, capability limits, grounding
requirements, or sandbox constraints. Learned preferences remain candidates
until explicitly confirmed.

Instruction records must not store hidden prompts, chain-of-thought, raw
secrets, raw headers, or domain-specific behavior. Conflict detection is
deterministic in v0.1 and records generic conflicts such as policy override
attempts, approval bypass attempts, style conflicts, grounding conflicts,
unsupported instructions, expired instructions, and duplicates.

The resolver returns an `InstructionResolutionResult` containing applied
instruction IDs, applied preference IDs, applied constraint IDs, suppressed
instruction IDs, effective instruction text, effective style, conflicts, and
constraints. It does not approve actions, change policy, change autonomy,
enable capabilities, or execute anything.
