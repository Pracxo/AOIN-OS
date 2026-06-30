# Platform Integration Closeout Checklist

## Required closeout checks

- docs complete
- examples valid
- scripts executable
- operator platform gates pass
- connector platform gates pass
- auth prototype review passes
- module design review passes
- connector no-go regressions pass
- auth and module no-go regressions pass
- static console remains preview-only
- SDK and CLI remain preview-only where documented
- no runtime enablement
- no operator write execution
- no connector implementation approval
- no production auth
- no external calls
- no credentials or tokens
- no sandbox execution
- no module activation
- no migrations
- no package files or lockfiles
- no API runtime execution routes
- no frontend dependencies
- no `aion-v0.1.0` tag movement

## Commands

```bash
./scripts/platform-integration-checkpoint.sh
./scripts/platform-integration-freeze-check.sh
./scripts/platform-integration-no-go-regression.sh
./scripts/check.sh
git diff --check
```

## Closeout decision

AION-117 can close only when every item is true and all implementation approval
booleans remain false.
