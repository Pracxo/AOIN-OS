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
