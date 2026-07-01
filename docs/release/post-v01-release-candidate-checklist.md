# Post-v0.1 Release Candidate Checklist

## Checklist

| Item | Required state |
| --- | --- |
| Docs complete | Required release docs and ADR 0109 exist |
| Examples valid | Release examples are valid synthetic JSON |
| Scripts executable | Release candidate scripts are executable |
| Operator gates passing | Operator regression and freeze gates pass |
| Connector gates passing | Connector regression and stabilization gates pass |
| Integration gates passing | Platform integration checkpoint, freeze, and no-go gates pass |
| No runtime implementation | Connector runtime, production auth, module activation, and write execution remain disabled |
| No external calls | External calls, external model calls, provider SDKs, network clients, and connector SDK dependencies remain absent |
| No credentials/tokens | Credential storage, token storage, OAuth, OIDC, and SAML runtime remain absent |
| No sandbox execution | Sandbox filesystem, network, process, dynamic import, package installation, and execution remain absent |
| No package files | Package manager files, lockfiles, frontend dependencies, and package install instructions remain absent |
| No migrations | Migration files remain unchanged and no migration is added |
| v0.1 tag untouched | `aion-v0.1.0` remains present and unchanged |
| v0.2 tag not created | No `v0.2`, `v0.2.0`, or `aion-v0.2.0` tag exists |

## Required Commands

```bash
./scripts/post-v01-release-candidate-gate.sh
./scripts/post-v01-release-candidate-freeze.sh
./scripts/post-v01-release-candidate-no-go-regression.sh
./scripts/check.sh
git diff --check
```

## Release Candidate Decision

The release candidate can be treated as passing only when every checklist item
is satisfied. Passing this checklist does not create a release and does not
approve v0.2 implementation.

## AION-119 Planning Closeout

AION-119 extends this checklist with v0.2 planning charter evidence, runtime
decision framework evidence, workstream mapping, ADR requirements, gate
dependency mapping, backlog intake criteria, and planning no-go regression.
The added planning evidence does not approve implementation or create a v0.2
release or tag.
