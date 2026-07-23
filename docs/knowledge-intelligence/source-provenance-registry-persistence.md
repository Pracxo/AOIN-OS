# Source Provenance Registry Persistence

AION-207 is authorized to define persistence semantics only for registry metadata. It is not authorized to add migrations, package files, runtime repositories, API routes, SDK resources, CLI commands, or background workers in AION-206. Any future persistence implementation remains subject to AION-207 scope and AION-208 closeout.

`maximum_persisted_source_body_bytes` is `0` and `maximum_repository_source_body_bytes` is `0`.
