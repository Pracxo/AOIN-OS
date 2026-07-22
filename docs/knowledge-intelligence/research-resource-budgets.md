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
