# Knowledge Intelligence Research Threat Model

Acquired content is untrusted evidence. Content instructions never override system policy. No acquired content becomes a verified fact merely because it was fetched.

## Required Threats

- SSRF
- DNS rebinding
- redirect escape
- private IP encoding bypass
- IPv6 bypass
- metadata-service access
- malicious DNS
- certificate failure
- malicious compression
- decompression bomb
- oversized response
- endless stream
- slow response
- content-type confusion
- charset confusion
- HTML active content
- executable download
- archive bomb
- PDF parser risk
- robots-policy ambiguity
- licensing ambiguity
- paywall bypass
- authentication leakage
- cookie leakage
- referer leakage
- private-content access
- prompt injection in acquired content
- source content instructing AION to ignore policy
- citation spoofing
- publication-date spoofing
- source-author spoofing
- mirrored-source duplication
- copied misinformation appearing independently corroborated
- SEO poisoning
- domain impersonation
- compromised authoritative source
- stale information
- changed pages
- retractions and corrections
- jurisdiction mismatch
- version mismatch
- source content promoted directly into memory
- user engagement treated as fact
- background crawler escape
- uncontrolled research cost
- evidence deletion
- source snapshot tampering
- research evidence mistaken for verified knowledge

## Core Controls

- prompt injection in acquired content is treated as untrusted content.
- source repetition does not equal corroboration.
- source classification does not establish truth.
- acquired evidence cannot override policy.
- research evidence cannot become verified knowledge automatically.

## AION-205 Controlled Research Acquisition Core

AION-205 implements the controlled research acquisition and immutable source-snapshot core as operator-invoked and runtime-disabled. Acquired content remains untrusted evidence; factual claim verification, knowledge promotion, cognitive belief mutation, public network fetch, crawler execution, search-provider integration, connector integration, source mutation, Git mutation, automatic merge, deployment, and model-weight training remain disabled. AION-204-KI-0001 is closed by AION-206; AION-206-KI-0002 is active for AION-207 source registry authorization.


## AION-206 source registry authorization

AION-206 records `RESEARCH_ACQUISITION_OPERATOR_EVALUATION_PASS_RECOMMEND_SOURCE_PROVENANCE_REGISTRY_AUTHORIZATION`, closes `AION-204-KI-0001`, and creates `AION-206-KI-0002` for AION-207 only. The source registry core is implemented as immutable in-memory metadata only; runtime, persistent registry writes, network, source body persistence, claim verification, knowledge promotion, and belief mutation remain disabled pending AION-208 formal closeout.
