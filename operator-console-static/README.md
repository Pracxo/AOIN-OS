# AION Operator Console Static Prototype

This directory contains the AION-089 static local Operator Console prototype.
It is plain HTML, CSS, and JavaScript only.

## Boundaries

- local read-only prototype
- no build step
- no frontend dependency
- no package manager file
- no runtime UI claim
- no production auth claim
- no activation
- no execution
- no external calls
- no stored protected values

## Run Locally

Open the file directly:

```bash
open operator-console-static/index.html
```

Serve it locally:

```bash
python3 -m http.server 8090 --directory operator-console-static
open http://localhost:8090
open "http://localhost:8090?api=http://localhost:8080"
```

Validate the static contract:

```bash
./scripts/operator-console-static-check.sh
./scripts/operator-console-static-demo.sh --offline-ok --skip-api
```
