# AION-243 Operator Runbook

Operators run the uninstalled local runner with:

- authorization: `AION-242-V02RQ-0003`
- confirmation: `BUILD_DETERMINISTIC_LOCAL_V02_RELEASE_CANDIDATE`
- candidate root policy: `user-home/.aion/release-candidates/<candidate-label>`

Supported commands are `preflight`, `build-candidate`, `verify-candidate`,
`audit-evidence` and `cleanup-temporary`. There are no publish, tag, release,
push, upload, deploy or promote commands.

AION-244 is required before any final v0.2 release decision.
