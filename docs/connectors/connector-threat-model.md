# Connector Threat Model

## Purpose

This threat model records connector risks before any connector runtime exists.
Every threat remains blocked in AION-106.

| Threat | Entry point | Current control | Future required control | No-go condition |
| --- | --- | --- | --- | --- |
| credential exfiltration | credential references, logs, examples, static console data | no credentials or tokens are stored | secret store, redaction, rotation, revocation, audit | credential value appears in repo, logs, examples, or static console |
| prompt injection through connector response | future connector ingress | no live connector responses are accepted | prompt-injection scan, provenance, operator review | connector response trusted without scan |
| malicious connector metadata | future connector manifest | metadata-only connector registry | manifest validation, trust classification, policy review | metadata activates runtime behavior |
| overbroad scopes | connector declaration | scopes are design-only | least-privilege policy and operator review | broad scope accepted without review |
| SSRF-style egress abuse | future connector destination | no external calls | destination allowlist and egress preview | unreviewed destination accepted |
| data exfiltration | future connector payload | external calls disabled | payload classification, redaction, policy, approval | protected data leaves without preview |
| stale response trust | future connector result | no live connector data | freshness labels and stale-data controls | stale data treated as authoritative |
| rate limit exhaustion | future connector call | no runtime call path | rate-limit enforcement and audit | rate limit absent or bypassed |
| audit tampering | connector event records | append-only audit posture | tamper-evident provenance and review | connector record can bypass audit |
| policy bypass | connector action request | no connector action runtime | fail-closed policy gate | connector self-authorizes |
| action authorization bypass | connector action proposal | dry-run action authorization remains separate | dry-run action authorization integration | connector executes without action authorization |
| hidden external calls | future connector runtime | runtime absent | no-external-call gate and release check | network client calls outside gate |
| provider impersonation | connector metadata or responses | no provider SDK or credential runtime | provider identity validation and provenance | connector claims provider identity without validation |
| dependency confusion | future connector package or SDK | no SDK dependency or package install | package trust and signed dependency model | connector SDK dependency added before gate |

## Design Decision

Connector runtime cannot proceed until every threat has a future control,
release gate evidence, and an operator-visible no-go condition.
