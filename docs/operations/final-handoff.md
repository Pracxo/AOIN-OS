# Final Local Handoff

AION v0.1 final handoff is a local verification and packaging flow. It does not
publish artifacts, deploy to cloud, enable full autonomy, or run domain modules.

Recommended sequence:

```bash
./scripts/check.sh
./scripts/release-candidate-check.sh
./scripts/package-release.sh
./scripts/verify-release-package.sh
./scripts/docker-up-core.sh
./scripts/kernel-self-test.sh
./scripts/aionctl.sh --scope workspace:main smoke run
./scripts/aionctl.sh --scope workspace:main release package --version 0.1.0 --dry-run
./scripts/aionctl.sh --scope workspace:main freeze run --version 0.1.0
```

The release handoff report records:

- included reports
- local verification commands
- known limits
- next steps
- generated timestamp

Known v0.1 limits:

- local-first only
- no production auth
- no cloud deployment
- no full autonomy by default
- no domain modules
- optional adapters disabled by default
- no untrusted code execution
- no raw secret storage

The handoff report is an operational artifact. It is not a deployment
approval, production certification, or domain-module readiness certificate.
