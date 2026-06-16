# 0052: Self Model and Capability Awareness

## Status

Accepted.

## Decision

AION Brain adds a Self Model and Capability Awareness layer for v0.1.

AION means Adaptive Intelligence Orchestration Nexus. AION OS means Adaptive
Intelligence Orchestration Nexus Operating System.

The self model is descriptive and diagnostic. It records what AION is, which
capabilities are active, which optional adapters are unavailable, which
limitations should be disclosed, and when deterministic confidence calibration
should add uncertainty disclosures.

Capability descriptions must come from awareness records, kernel diagnostics,
configuration, and local service status. They must reflect actual active,
disabled, unavailable, dry-run, or optional states.

Confidence calibration is deterministic in v0.1. It uses local references such
as evidence, beliefs, memory, limitations, grounding requirements, and response
metadata. It does not call model providers.

## Reason

AION needs an accurate self-description and limitation awareness before broader
operator, SDK, dialogue, and module use. Centralizing this avoids hard-coded
capability claims in UI, CLI, SDK, dialogue, and operator surfaces.

## Consequences

Dialogue, Operator Control Tower, SDK, CLI, diagnostics, and response
verification can answer capability and limitation questions through AION-owned
contracts. Unsupported capability claims can be detected before responses are
treated as verified.

Future domain modules can add capability manifests, but Brain core remains
generic and describes only governed contracts and local adapter status.

## Constraints

The self model must not claim sentience, personality, production readiness,
full autonomy, domain expertise, or unavailable external integrations.

The self model must not execute capabilities, override policy, override
autonomy, approve actions, enable adapters, mutate runtime configuration,
promote skills, or invent capabilities.

No domain-specific capability claims or workflow logic belong in Brain core.
