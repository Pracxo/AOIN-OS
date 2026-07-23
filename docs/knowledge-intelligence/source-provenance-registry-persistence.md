# Source Provenance Registry Persistence

AION-207 implements persistence semantics as fail-closed write-disabled behavior. `maximum_registry_write_batch` remains `0`, so the registry may project metadata and simulate append in memory but cannot apply a persistent write.

The implementation adds no migrations, package files, runtime repositories, API routes, SDK resources, CLI commands, schedulers, startup hooks, or background workers. Any future persistent registry store requires a separate authorization after AION-208 closeout.

`maximum_persisted_source_body_bytes` is `0` and `maximum_repository_source_body_bytes` is `0`.
