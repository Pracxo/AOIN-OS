# Connector Sandbox Isolation Model

The connector sandbox isolation model is fail-closed. AION can describe a
future sandbox boundary, inspect declared capability requests, and return
readiness evidence, but it cannot run sandboxed connector code.

Isolation rules:

- No filesystem read or write surface is exposed.
- No inbound or outbound network surface is exposed.
- No credential or token surface is exposed.
- No process, shell, package install, or dynamic import surface is exposed.
- No connector activation or runtime registration surface is exposed.
- No SDK command or API route performs provider calls or connector calls.

The isolation service returns local evidence only. It emits visual telemetry
for operator visibility and records readiness audit metadata when the preview
gate is evaluated.
