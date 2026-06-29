# Static Console Safety Matrix

| control | checked by script | evidence | release blocker if failed |
| --- | --- | --- | --- |
| no frontend dependencies | `static-console-safety-check.sh` | package and lock files are absent | yes |
| no build step | `static-console-safety-check.sh` | Vite, Next, Tailwind, and webpack configs are absent | yes |
| no external scripts | `static-console-safety-check.sh` | `index.html` has no external script source | yes |
| localhost-only API | `static-console-safety-check.sh` | `app.js` keeps `isLocalApiOrigin` and blocks non-local origins | yes |
| read-only view models | `operator-console-static-check.sh` | demo JSON keeps `read_only=true` | yes |
| no write verbs | `static-console-safety-check.sh` | `app.js` has no `PUT`, `PATCH`, or `DELETE` method | yes |
| no activation controls | `static-console-safety-check.sh` | dangerous activation buttons are absent or disabled no-go labels | yes |
| no execution controls | `static-console-safety-check.sh` | dangerous execution buttons are absent or disabled no-go labels | yes |
| no provider call controls | `static-console-safety-check.sh` | provider-call buttons and external URLs are absent | yes |
| no login form | `static-console-safety-check.sh` | `index.html` has no form or login input | yes |
| no credential inputs | `static-console-safety-check.sh` | password, token, cookie, and credential inputs are absent | yes |
| no token/cookie/session persistence | `static-console-safety-check.sh` | auth and session demo flags remain false | yes |
| no raw prompt display | `static-console-safety-check.sh` | protected prompt keys are redaction keys only | yes |
| no hidden reasoning display | `static-console-safety-check.sh` | hidden reasoning is redacted before rendering | yes |
| no secret display | `static-console-safety-check.sh` | secret-like demo markers are blocked | yes |
| demo fallback | `static-console-safety-check.sh` | `loadDemo` and `demo-data` fallback references remain present | yes |
| stabilization freeze gate | `operator-platform-freeze-gate.sh` | AION-102 regression and freeze evidence remain passed | yes |
