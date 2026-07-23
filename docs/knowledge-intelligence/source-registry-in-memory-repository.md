# Source Registry In-Memory Repository

`InMemorySourceRegistryRepository` is the only AION-207 repository implementation.

It is constructed from immutable registry envelopes and exposes read-only operations:

- `snapshot()`
- `records()`
- `record_count()`
- exact `record_by_id()`
- pure `with_simulated_append(...)`

`with_simulated_append(...)` returns a new repository object. The original repository remains unchanged.

The repository has no global singleton, mutable shared dictionary, background worker, scheduler, file I/O, network I/O, database connection, migration, save, update, delete, truncate, compact, overwrite, source mutation, Git mutation, PR, approval, merge, deployment, or model-provider behavior.
