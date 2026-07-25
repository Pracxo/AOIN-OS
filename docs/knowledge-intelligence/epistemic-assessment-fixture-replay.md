# Epistemic Assessment Fixture Replay

Fixture replay requires an explicit operator-supplied absolute path outside the canonical repository. Relative paths, repository descendants, hidden paths, symlinks, directories, device paths, URI syntax, environment expansion, home expansion, oversized files, invalid UTF-8, invalid JSON, extra fields, source bodies, and protected material are rejected.

Replay reconstructs only in-memory source-registry and claim-graph repositories, audits integrity, runs deterministic assessment, creates no tracked state, and applies no persistent write.
