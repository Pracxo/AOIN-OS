# Source Registry Contracts

The AION-207 contract module is `services/brain-api/src/aion_brain/contracts/knowledge_source_registry.py`.

It defines strict frozen Pydantic v2 models with `extra=forbid` and hidden rejected inputs. Contract constants bind the program, authorization, implementation task, formal closeout task, scope, schema versions, reason-code registry, and exact AION-206 resource limits.

Authorized payload kinds are:

- `source_snapshot_digest`
- `source_provenance`
- `citation_reference`
- `source_lineage`
- `deduplication_decision`
- `policy_decision`
- `operator_review_reference`

Every payload is metadata-only. Raw source bodies, redacted previews as content, raw URL query values, credentials, tokens, cookies, authorization headers, private keys, raw prompts, hidden reasoning, raw user messages, personal data, source patches, raw diffs, executable commands, and runtime effects are rejected.

No contract represents a verified fact, verified claim, promoted knowledge item, created belief, mutated belief, active runtime, or applied persistent write.
