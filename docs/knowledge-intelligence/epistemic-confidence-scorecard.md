# Epistemic Confidence Scorecard

The future AION-211 scorecard must be deterministic, transparent, and versioned. It may use the approved dimensions in `examples/knowledge-intelligence/epistemic-scorecard.json`.

## Hard Caps

- `zero_independent_evidence_groups`: `{'maximum_confidence': 0.2}`
- `one_independent_evidence_group`: `{'maximum_confidence': 0.6}`
- `only_unknown_or_community_unverified_evidence`: `{'maximum_confidence': 0.5}`
- `missing_citation_coverage`: `{'maximum_confidence': 0.45}`
- `incomplete_provenance`: `{'maximum_confidence': 0.5}`
- `stale_evidence`: `{'maximum_confidence': 0.5}`
- `unresolved_material_opposition`: `{'status': 'mixed', 'maximum_confidence': 0.65}`
- `scope_mismatch`: `{'status': 'scope_mismatch', 'maximum_confidence': 0.2}`
- `insufficient_explicit_scope`: `{'status': 'insufficient_evidence'}`
- `applicable_retraction`: `{'status': 'retracted'}`
- `applicable_supersession_without_current_support`: `{'status': 'superseded'}`
- `broken_source_registry_or_graph_integrity`: `{'status': 'unknown', 'confidence': 0}`

Source class alone cannot establish support, and evidence quantity cannot override scope mismatch, retraction, broken integrity, unresolved contradiction, or lack of independent sources.
