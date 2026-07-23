# Knowledge Intelligence Research Resource Budgets

AION-204 authorizes these maximum future AION-205 limits. AION-204 itself performs zero research network calls.

```json
{
  "approvals_created_by_runtime": 0,
  "background_crawls": 0,
  "cognitive_belief_mutations": 0,
  "git_operations": 0,
  "knowledge_promotions": 0,
  "maximum_citation_references_per_snapshot": 20,
  "maximum_concurrency": 4,
  "maximum_domains_per_plan": 20,
  "maximum_fetches_per_plan": 50,
  "maximum_queries_per_plan": 20,
  "maximum_redirects_per_fetch": 3,
  "maximum_response_bytes_per_source": 5242880,
  "maximum_safe_headers_per_snapshot": 32,
  "maximum_snapshot_records_per_plan": 100,
  "maximum_source_candidates_per_plan": 100,
  "maximum_timeout_seconds_per_request": 20,
  "maximum_total_transfer_bytes_per_plan": 52428800,
  "maximum_wall_clock_seconds_per_plan": 900,
  "model_weight_changes": 0,
  "network_calls_during_AION_204": 0,
  "production_exposure": 0,
  "real_pull_requests_created_by_runtime": 0,
  "research_runtime_enabled": false,
  "scheduled_research_runs": 0,
  "source_mutations": 0
}
```

Any violation must fail closed, stop the research plan, discard partial unvalidated outputs, preserve a redacted incident record, create no knowledge candidate, create no belief, create no approval, create no authorization, and create no runtime effect.

A source-quality score cannot override a security or budget violation.

## AION-205 Controlled Research Acquisition Core

AION-205 implements the controlled research acquisition and immutable source-snapshot core as operator-invoked and runtime-disabled. Acquired content remains untrusted evidence; factual claim verification, knowledge promotion, cognitive belief mutation, public network fetch, crawler execution, search-provider integration, connector integration, source mutation, Git mutation, automatic merge, deployment, and model-weight training remain disabled. AION-204-KI-0001 is closed by AION-206; AION-206-KI-0002 is active for AION-207 source registry authorization.

## Exact AION-205 Limits

- `approvals_created_by_runtime=0`
- `background_crawls=0`
- `cognitive_belief_mutations=0`
- `git_operations=0`
- `knowledge_promotions=0`
- `maximum_citation_references_per_snapshot=20`
- `maximum_concurrency=4`
- `maximum_domains_per_plan=20`
- `maximum_fetches_per_plan=50`
- `maximum_operator_review_items_per_plan=50`
- `maximum_queries_per_plan=20`
- `maximum_redirects_per_fetch=3`
- `maximum_response_bytes_per_source=5242880`
- `maximum_safe_headers_per_snapshot=32`
- `maximum_snapshot_records_per_plan=100`
- `maximum_source_candidates_per_plan=100`
- `maximum_timeout_seconds_per_request=20`
- `maximum_total_transfer_bytes_per_plan=52428800`
- `maximum_wall_clock_seconds_per_plan=900`
- `model_weight_changes=0`
- `network_calls_during_AION_204=0`
- `network_calls_permitted=0`
- `production_exposure=0`
- `real_pull_requests_created_by_runtime=0`
- `research_runtime_enabled=false`
- `scheduled_research_runs=0`
- `source_mutations=0`


## AION-206 source registry authorization

AION-206 records `RESEARCH_ACQUISITION_OPERATOR_EVALUATION_PASS_RECOMMEND_SOURCE_PROVENANCE_REGISTRY_AUTHORIZATION`, closes `AION-204-KI-0001`, and creates `AION-206-KI-0002` for AION-207 only. The source registry core is implemented as immutable in-memory metadata only; runtime, persistent registry writes, network, source body persistence, claim verification, knowledge promotion, and belief mutation remain disabled pending AION-208 formal closeout.
