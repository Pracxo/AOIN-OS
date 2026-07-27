# AION-219 Controlled Public Research Pilot Implementation

AION-219 implements the AION-218-KI-0008 controlled operator-invoked public HTTPS research pilot. The pilot accepts explicit research plans, explicit HTTPS source candidates, exact domain allowlists, and explicit claim specifications.

Implemented controls:

- public DNS resolution through explicit backends with disabled defaults
- public-address validation, DNS pinning, DNS rebinding defence, and peer verification
- pinned HTTPS transport with certificate verification, hostname verification, SNI, TLS 1.2 minimum, and no proxy inheritance
- fixed GET and HEAD request headers with `Accept-Encoding: identity`
- manual redirect handling with destination revalidation and loop/downgrade rejection
- robots and X-Robots policy validation
- licence and source-class policy validation
- prompt-injection markers treated as untrusted source data
- source-body bytes purged from returned records after redacted fingerprints and evidence metadata are built
- full Knowledge Intelligence lineage trace across acquisition, source registry, claim graph, assessment, domain mesh, simulation-only tool verification, and verified-candidate memory
- operator review required for every candidate

Runtime boundary: `runtime_effect=false`, `public_network_fetch_enabled=false`, `background_network_access_enabled=false`, `background_crawler_enabled=false`, `search_provider_integration_enabled=false`, `connector_integration_enabled=false`, `model_provider_integration_enabled=false`, `browser_automation_enabled=false`, `automatic_verified_knowledge_promotion_enabled=false`, `persistent_verified_knowledge_write_enabled=false`, `cognitive_memory_write_enabled=false`, `belief_mutation_enabled=false`, and `production_exposure=false`.

Live validation evidence:

- mode: `operator_invoked_live`
- status: `completed`
- external read performed: `true`
- explicit source candidates: `3`
- source control groups: `3`
- DNS resolutions: `4`
- public HTTPS requests: `4`
- robots requests: `1`
- redirects: `0`
- successful sources: `3`
- operator-review candidate count: `1`
- candidate status: `eligible_for_operator_review`
- source bodies retained: `0`
- source bodies persisted: `0`
- automatic promotions: `0`
- cognitive memory writes: `0`
- belief mutations: `0`
- persistent verified-knowledge writes: `0`
- report fingerprint: `2ecdcc382d06abd180671dce0972982d68f2fbb9acab7d169ce26374c57bb258`

The committed live evidence is a redacted summary only: `examples/knowledge-intelligence/public-research-pilot-live-evidence-redacted.json`.

AION-218-KI-0008 remains active, non-consumed, non-expired, and non-reusable pending AION-220 formal evaluation and closeout.
