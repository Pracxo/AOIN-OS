# ADR 0034: Policy Catalog, Permission Matrix, and Rego Test Harness

## Decision

AION Brain v0.1 adds a backend policy governance layer made of a generic policy
action catalog, permission catalog, reusable role templates, side-effect-free
policy simulations, deterministic policy test cases, coverage reports, policy
bundle exports, and OPA status checks.

The catalog is Brain-owned and domain-neutral. It records the policy vocabulary
that AION core recognizes, but it does not introduce finance, trading, IT,
legal, healthcare, HR, procurement, or other vertical policies.

## Reason

The Brain needs visible governance before more runtime autonomy is added.
Catalogued actions, permissions, role templates, tests, and bundles make policy
behavior auditable and reproducible without requiring a live OPA service during
unit tests.

## Constraints

- All policy actions and permissions use generic dotted lowercase names.
- Modules never self-authorize.
- Unknown policy actions fail closed.
- Policy simulation never executes the target action.
- Policy tests use fakes and do not require live OPA.
- Bundle exports must not contain raw secrets.
- Rego remains behind the policy adapter boundary.
- Domain-specific policy vocabularies live outside Brain core later.

## Consequences

Future AION modules can inspect the generic permission matrix and policy test
results before integration. Policy bundles can be exported for review,
regression, and environment comparison while public Brain contracts remain
independent of OPA internals.
