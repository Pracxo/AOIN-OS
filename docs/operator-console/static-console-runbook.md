# Static Console Runbook

## Local file preview

```bash
open operator-console-static/index.html
```

This opens the prototype directly from disk. If the local API request is not
available from the browser context, the page renders demo JSON.

## Local static server

```bash
python3 -m http.server 8090 --directory operator-console-static
open http://localhost:8090
open "http://localhost:8090?api=http://localhost:8080"
```

The `api` parameter is optional. Only `localhost` and `127.0.0.1` origins are
accepted. Any other origin is blocked and replaced with offline demo data.

## Verification commands

```bash
./scripts/operator-console-static-check.sh
./scripts/operator-console-static-demo.sh --offline-ok
./scripts/operator-console-static-demo.sh --offline-ok --skip-api
```

The demo script prints the static-server command. It does not start a
long-running server unless `--serve` is passed.

## API-offline behavior

If the Brain API is unavailable and `--offline-ok` is present, the demo script
returns success with offline instructions. This is expected for a local static
prototype because demo JSON is a first-class fallback.

## API-connected behavior

When the API is reachable and `--skip-api` is not present, the demo script
checks `/health` and then requests `/brain/operator-console/view-model`.
Unavailable view-model responses are warnings only when `--offline-ok` is
present. Real online checks are not weakened when offline mode is not enabled.

## Safety checks

The static check validates:

- required files exist
- demo JSON is valid and synthetic
- no package manager file is introduced
- the read-only banner is present
- the API guard accepts only local origins
- non-local origins are blocked
- write methods are absent
- external script and stylesheet imports are absent
- redaction terms are present in `app.js`
- ADR 0080 is indexed
