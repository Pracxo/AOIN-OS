# Model Gateway Runtime Hold

AION-233 keeps the model gateway under runtime hold pending AION-234 formal
evaluation and authorization closeout.

Runtime hold assertions:

- Gateway implemented: true.
- Reference provider available: true.
- Actual provider calls: false.
- Provider network egress: false.
- Provider SDK: false.
- Provider credentials: false.
- API keys and tokens: false.
- Authorization headers: false.
- Live model sessions: false.
- Prompt persistence: false.
- Response persistence: false.
- Hidden reasoning retention: false.
- Raw provider payload retention: false.
- Tool calls: false.
- Function calls: false.
- Connector execution: false.
- Browser, shell, subprocess, and module execution: false.
- Production memory writes: false.
- Production policy mutation: false.
- Belief mutation: false.
- Source rewrite: false.
- Deployment: false.
- Model training: false.
- Production exposure: false.
- v0.2 release readiness: false.

The runtime hold script invokes the AION-233 implementation check and defers
the full aggregate repository check when already running inside pytest or an
outer aggregate gate.
