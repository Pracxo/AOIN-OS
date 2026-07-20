# Shadow-Mode Output And Retention

The runner writes no file by default. When an operator supplies an output
directory, it must be absolute, existing, non-hidden, outside the canonical
repository, and resolved strictly. Repository root and repository descendants
are rejected. Existing files are not overwritten.

Output is serialized before writing, checked against byte and file-count
budgets, and written with exclusive creation. The preferred operator-managed
root is `/tmp/aion-shadow-mode/`, but AION-178 does not create it.

In-memory results use a per-instance `EphemeralShadowStore`. Retention defaults
to 86400 seconds and cannot exceed 604800 seconds. Purge is explicit only; no
background cleanup is registered.
