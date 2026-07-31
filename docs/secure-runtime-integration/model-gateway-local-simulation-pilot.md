# Model Gateway Local Simulation Pilot

Pilot ID: `AION-233-controlled-model-gateway-simulation-pilot`.

The pilot validates one local deterministic model-gateway session under
`AION-232-SRI-0002`. It binds the AION-231 secure-runtime component, verifies
parent capability `brain.think.simulate`, requires guard outcome
`allow_simulation`, loads one provider manifest, loads two model manifests,
processes one text simulation request, processes one structured JSON simulation
request, performs exact replay, rejects changed replay, rejects protected
material, rejects smuggled action output, validates outputs, records
provenance, audits integrity, closes all requests, closes the gateway session,
and removes temporary files.

Committed evidence is
`examples/secure-runtime-integration/model-gateway-local-simulation-pilot-evidence.json`.
It records report fingerprint
`d911ecc911b0f5833770629eb77fdfb42e6718c80c894984fb43f0e0a11d0982`, one
provider manifest, two model manifests, one started and closed session, two
processed requests, two successful response validations, one exact replay, one
changed replay rejection, one protected-material rejection, one smuggled-action
rejection, zero active sessions after close, zero active requests after close,
zero temporary files retained, and zero prohibited-effect counters.
