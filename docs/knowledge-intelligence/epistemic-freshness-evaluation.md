# Epistemic Freshness Evaluation

Freshness is deterministic and uses the request's explicit policy. Modification timestamp is preferred, publication timestamp is second, and retrieval timestamp never proves content freshness. Missing publication and modification timestamps produce `unknown`.

Future timestamps beyond tolerance are treated as unsafe evidence posture. Stale, superseded, and retracted evidence cannot bypass hard caps.
