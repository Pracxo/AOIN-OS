# Connector Policy Traceability

Connector policy traceability links catalog actions, authorization matrix rows,
dry-run results, denial rules, audit evidence, and connector safety docs.

Traceability rows include:

- connector key
- action key
- policy references
- matrix references
- evidence references
- dry-run references
- denial references
- audit references
- status

The traceability endpoint is read-only. It does not inspect live connectors,
does not call external systems, does not load connector code, and does not
persist connector runtime state.

The static console uses demo traceability data only. Runtime and external call
paths remain absent.
