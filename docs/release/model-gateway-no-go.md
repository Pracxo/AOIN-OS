# Model Gateway No-Go

The AION-233 no-go gate preserves the authorized source scope and rejects
runtime surfaces outside the deterministic local model-gateway implementation.

Rejected changes include AION-231 runtime source, production-auth source,
workflows, dependency files, migrations, API routes, middleware, startup hooks,
schedulers, workers, provider SDK imports, network-client imports, credential
or token stores, endpoint or authorization-header creation, streaming clients,
tool/function execution, connector imports, shell/subprocess/browser imports,
module loading, prompt persistence, response persistence, raw provider-payload
retention, production writes, memory or belief effects, source deletion, source
rename, v0.2 tags, and v0.2 releases.

The gate allows only the exact AION-233 model-gateway source paths plus tests,
scripts, docs, examples, and static-console evidence needed for this task. It
does not weaken the inherited AION-232 authorization checks.
