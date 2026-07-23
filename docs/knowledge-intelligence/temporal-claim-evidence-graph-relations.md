
# Temporal Claim-Evidence Graph Relations

Allowed claim relation assertions are equivalent_to, refines, supersedes, corrects, retracts, duplicate, and structural_conflict_candidate. Evidence roles are supports, opposes, context, and duplicate.

Relation edges remain assertions. They do not establish truth. A structural conflict candidate can mark incompatible object or polarity under overlapping time, jurisdiction, and version scope, but it must never emit one_claim_true=true or one_claim_false=true.
