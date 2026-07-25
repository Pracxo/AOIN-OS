# Epistemic Assessment Request Model

An AION-211 request contains only safe IDs and explicit policy objects. It requires a request ID, 1 to 500 unique claim IDs, an explicit target valid-time interval, explicit jurisdiction IDs, explicit version scopes, an explicit freshness policy, and a UTC assessment time.

Unspecified target scope is insufficient. Unspecified never means global and never means all versions. Requests are operator-supplied, synthetic, read-only, redacted, and have `runtime_effect=false`.
