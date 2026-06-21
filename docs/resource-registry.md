# Global Resource Registry and Link Integrity

AION Global Resource Registry is a Brain-owned index and integrity layer. It
normalizes references across Brain-owned resources into safe descriptors and
directed links. It is not the source of truth for indexed records.

## Resource URI

Canonical resource URIs use:

```text
aion://{resource_type}/{resource_id}
aion://{resource_type}/{resource_id}?trace_id={trace_id}
```

The URI identifies the resource for registry indexing and link integrity. It
does not grant access, imply ownership transfer, or expose source-system
internals.

## Indexed Records

The registry stores:

- `ResourceDescriptor`
- `ResourceIndexRecord`
- `ResourceReferenceLink`
- `BrokenReference`
- `OrphanedResource`
- `ReferenceValidationRun`
- `RegistryRebuildRun`
- `RegistrySnapshot`

Descriptors are redacted before indexing. Registry records reject secret-like
payloads and hidden-instruction markers.

## Link Integrity

Reference validation checks indexed links and can record broken references,
stale references, missing targets, and orphaned resources. Validation does not
repair source records. Dismissal changes the registry-owned finding state only.

Backlinks are computed from registry-owned links. They are a navigation aid,
not an authoritative source graph.

## Rebuilds and Snapshots

Registry rebuilds read local safe descriptors from configured Brain services
and refresh the registry-owned index. They do not mutate or delete source
records. `clear_missing` only affects registry index state.

Snapshots record deterministic counts, type summaries, source summaries, and a
root hash for registry-owned metadata. Snapshots are local audit artifacts.

## Operator and Telemetry

The Operator Control Tower can show a Resource Registry status card and queues
for broken references, orphaned resources, and rebuild runs. The registry can
emit generic visual telemetry such as `resource_indexed`,
`resource_link_created`, `broken_reference_detected`,
`orphaned_resource_detected`, `registry_rebuild_started`,
`registry_rebuild_completed`, and `registry_snapshot_created`.

## Boundaries

The registry must not:

- become the source of truth for indexed resources
- mutate source records
- repair source references
- hard-delete source records
- call external services
- depend on search or graph databases
- expose raw headers, hidden reasoning, raw prompts, provider payloads, or secrets
- add domain-specific resource logic

All registry APIs return AION-owned contracts only.
