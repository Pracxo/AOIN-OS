# Secure Runtime Integration No-Go

AION-230 is no-go if it creates or enables any runtime implementation surface.
AION-230-SRI-0001 authorizes only AION-231, and AION-232 must perform the
formal closeout before any successor authorization.

## No-Go Conditions

- AION-231 runtime source exists in the AION-230 branch.
- Production-auth, request-identity, ActorContext, replay-protection, GLM,
  Knowledge Intelligence, self-improvement, connector, module, or model-gateway
  runtime source changes are present in the AION-230 branch.
- Package files, lockfiles, migrations, API routes, installed CLI commands,
  startup hooks, schedulers, workers, or workflow changes are added.
- Network imports, credential stores, token stores, authentication endpoints,
  session-token issuance, provider calls, connector calls, tool execution,
  shell execution, subprocess execution, browser automation, module activation,
  production writes, source mutation, Git mutation, deployment, model training,
  v0.2 tags, or v0.2 releases are introduced.
- `implementation_approved=true` is created for any future SRI task beyond
  AION-231.
- More than one active SRI authorization exists.

Every no-go condition fails closed.
