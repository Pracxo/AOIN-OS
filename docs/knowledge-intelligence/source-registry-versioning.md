# Source Registry Versioning

AION-207 uses immutable correction records rather than in-place updates.

An initial record has `record_version=1` and no supersession reference.

A correction:

- creates a new record ID
- increments `record_version` by one
- references the superseded record
- preserves the superseded record
- preserves all prior fingerprints
- preserves sequence ordering
- never mutates prior payloads
- never deletes or hides historical metadata

The registry rejects same-ID changed payloads, missing superseded records, version rollback, version jumps, self-supersession, supersession cycles, source-body introduction, truth state introduction, knowledge promotion, and belief mutation.
