# Operator Console Integration Route Manifest

Authorization: `AION-236-SRI-0004`
Implementation task: `AION-237`
Formal closeout: `AION-238`

AION-236 records this authorization only. It creates no AION-237 runtime source, no loopback listener, no route registration and no live bridge behavior.

Authorized route count: `10`. Static asset allowlist: `/, /index.html, /styles.css, /app.js, /live-console.js`.

Required boundary: loopback-only, same-origin, exact Host validation, ephemeral mutation nonce for POST requests, redacted projections, explicit operator confirmations for state-changing requests, and zero external or production effects.

Prohibited capabilities remain false: public listening, external egress, DNS, browser persistence, provider calls, external connectors, real tools, filesystem writes, process execution, production writes, deployment, model training, v0.2 tag creation and v0.2 release creation.
