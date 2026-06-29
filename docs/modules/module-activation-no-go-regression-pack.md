# Module Activation No-Go Regression Pack

## Purpose

The no-go regression pack defines the checks that must remain green before any
future activation implementation can start. AION-105 keeps all no-go checks in
the expected blocked state.

## No-Go Checks

- code loader added
- package installer added
- dynamic import added
- runtime route registration added
- capability activation enabled
- external dependency download added
- executable payload accepted
- controlled execution enabled
- module writes enabled
- `activation_ready=true` by default
- policy bypass
- audit bypass

## Expected Result

Every no-go check must pass by proving the unsafe behavior is absent. A passing
result does not approve activation; it only proves the repository still blocks
activation.

## Local Command

```bash
./scripts/module-activation-no-go-regression.sh
```

Expected result:

```text
Module activation no-go regression PASS
```
