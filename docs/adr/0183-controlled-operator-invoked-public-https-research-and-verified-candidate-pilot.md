# 0183: Controlled Operator-Invoked Public HTTPS Research and Verified-Candidate Pilot

Status: Accepted

AION-219 implements a bounded operator-invoked public HTTPS pilot under AION-218-KI-0008. The decision is to keep system DNS and pinned HTTPS available only through explicit runner construction, while defaults remain disabled and no production runtime, crawler, search provider, connector, model provider, browser, persistent write, cognitive-memory write, belief mutation, or automatic promotion is enabled.

The pilot requires explicit plans, explicit HTTPS source candidates, exact domain allowlists, explicit claim specifications, public-address validation, DNS pinning, TLS certificate and hostname verification, peer verification, redirect revalidation, robots and content policy, source-body purge, complete redacted lineage, and operator review.
