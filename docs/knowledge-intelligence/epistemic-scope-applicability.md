# Epistemic Scope Applicability

AION-211 evaluates valid-time, jurisdiction, and version applicability against the explicit request target scope. Valid-time and version overlap reuse AION-209 temporal helpers. Global jurisdiction must be explicit. Parent jurisdiction can only produce partial applicability when explicitly represented.

Scope mismatch forces `scope_mismatch` and caps confidence at 0.20. Insufficient explicit scope forces `insufficient_evidence` and requires abstention.
