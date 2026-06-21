# 0063: Global Resource Registry and Link Integrity

## Status

Accepted

## Context

AION Brain now has many local records that refer to one another through trace
IDs, record IDs, evidence references, audit references, and operator-facing
surfaces. The system needs a common reference spine without making any one
projection layer the source of truth.

## Decision

Add a Brain-owned Global Resource Registry that indexes safe descriptors,
resource links, backlinks, broken references, orphaned resources, validation
runs, rebuild runs, and snapshots.

Resource identity uses AION-owned URIs:

```text
aion://{resource_type}/{resource_id}
aion://{resource_type}/{resource_id}?trace_id={trace_id}
```

The registry is an index and integrity layer only. Source systems remain
authoritative for their own records. Registry validation reports findings.
Registry rebuilds refresh registry-owned index records from local safe
descriptors. Neither path repairs, mutates, or hard-deletes source records.

## Consequences

Future Brain layers can refer to resources through a stable AION URI format.
Operator, audit, visual telemetry, release, backup, and incident surfaces can
show reference integrity without importing source-system internals.

Registry records may become stale if source systems change without an indexing
pass. Validation and rebuild runs make that state explicit without pretending
to repair it automatically.

## Constraints

- The registry is not the source of truth.
- No source record mutation.
- No source reference repair.
- No hard deletes of source records.
- No external service calls.
- No search or graph database dependency.
- No domain-specific resource logic.
- Public APIs return AION-owned contracts only.
