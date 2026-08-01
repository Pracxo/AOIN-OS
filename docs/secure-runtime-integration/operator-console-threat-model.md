# Operator Console Integration Threat Model

Authorization: `AION-236-SRI-0004`
Implementation task: `AION-237`
Formal closeout: `AION-238`

AION-237 implements this authorization as a same-origin loopback-only local bridge with no public listener, external egress, browser persistence, production route registration or live-provider behavior. AION-238 remains the formal closeout.

Authorized route count: `10`. Static asset allowlist: `/, /index.html, /styles.css, /app.js, /live-console.js`.

Required boundary: loopback-only, same-origin, exact Host validation, ephemeral mutation nonce for POST requests, redacted projections, explicit operator confirmations for state-changing requests, and zero external or production effects.

Prohibited capabilities remain false: public listening, external egress, DNS, browser persistence, provider calls, external connectors, real tools, filesystem writes, process execution, production writes, deployment, model training, v0.2 tag creation and v0.2 release creation.
