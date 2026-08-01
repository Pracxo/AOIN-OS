# AION-237 checklist

Authorization: `AION-236-SRI-0004`.
Implementation task: `AION-237`.
Formal closeout: `AION-238`.

AION-237 implements a controlled same-origin loopback Operator Console bridge. It binds only to `127.0.0.1`, serves the five injected static assets, exposes only the ten authorized `/aion/local/v1/` routes, and requires exact Host, Origin, content type, operator confirmation and ephemeral mutation nonce checks for state-changing requests.

The bridge composes the already implemented AION-231 secure runtime, AION-233 deterministic reference model gateway and AION-235 sandboxed reference capability runtime through redacted local projections. Model output is untrusted proposal material only. Capability and connector requests require explicit operator selection and confirmation.

Runtime boundaries remain closed: public listening, DNS resolution, external egress, cookies, browser storage, credential input, token issuance, live provider calls, external connectors, real tools, filesystem writes, process execution, production memory, production policy, belief mutation, source rewrite, deployment, model training, v0.2 tags and v0.2 releases are not enabled.

Pilot evidence: `examples/secure-runtime-integration/operator-console-integrated-local-runtime-pilot-evidence.json`.
Report fingerprint: `e54ea6886c6d7f56c1de568983515944b1b72b3dc2d8f59b310039bb96ed5035`.

## Checklist

- [x] Ten exact local routes.
- [x] Five exact injected static assets.
- [x] Same-origin Host and Origin enforcement.
- [x] Ephemeral mutation nonce issue, rotate and invalidate.
- [x] Text and structured deterministic model simulations.
- [x] Three reference capabilities.
- [x] Synthetic connector read and write preview.
- [x] Kill-switch negative control.
- [x] Session close and listener cleanup.
- [x] All prohibited-effect counters zero.
- [x] AION-236-SRI-0004 remains active for AION-238.
- [x] v0.2 remains unreleased.
