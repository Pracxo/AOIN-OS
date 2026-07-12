# v0.2 Explicit Approval Record Schema

## Purpose

AION-147 defines the explicit approval record shape required before future
implementation authorization can be considered. This schema is preview-only and
does not approve implementation.

## Required Fields

| Field | Required default | Notes |
| --- | --- | --- |
| `approval_record_id` | string | Stable identifier for the future approval record. |
| `candidate_id` | string | Candidate implementation or runtime capability request. |
| `workstream` | string | Owning v0.2 workstream. |
| `requested_runtime_capability` | string | Capability requested for future runtime use. |
| `approval_status` | `false` | Must remain false in AION-147. |
| `implementation_authorization_status` | `false` | Must remain false in AION-147. |
| `runtime_guard_release_status` | `false` | Must remain false in AION-147. |
| `approved_by` | empty | No approver is assigned in this preview. |
| `reviewers` | list | Reviewer identities may be planned but do not approve implementation. |
| `required_adr` | string | Required ADR dependency for any future candidate. |
| `required_gate` | string | Required gate dependency for any future candidate. |
| `evidence_refs` | list | Evidence references for future review. |
| `security_review_refs` | list | Security review evidence references. |
| `architecture_review_refs` | list | Architecture review evidence references. |
| `operator_review_refs` | list | Operator review evidence references. |
| `rollback_plan_ref` | string | Rollback plan reference required before approval. |
| `audit_provenance_ref` | string | Audit/provenance record reference. |
| `expiry` | string | Expiry window for future authorization. |
| `revocation_path` | string | Revocation process reference. |
| `no_go_acknowledgement` | `true` | The current no-go state must be acknowledged. |
| `created_at` | string | Synthetic creation timestamp in examples. |
| `metadata` | object | Non-secret preview metadata only. |

## Default Values

- `approval_status=false`
- `implementation_authorization_status=false`
- `runtime_guard_release_status=false`

## Boundary

`explicit_approval_record_created=true` only confirms that a schema exists.
`explicit_approval_record_approval=false` remains the controlling state. The
schema does not enable runtime, release guards, operator write execution,
connector runtime, production auth, module activation, external calls,
credential storage, token storage, or sandbox execution.

## AION-148 Implementation Authorization Stabilization

AION-148 freezes the implementation authorization preview, explicit approval
record schema, and runtime enablement guard boundary into a stable evidence
baseline. It remains non-approving: `implementation_authorization_preview_only=true`,
`implementation_authorization_approved=false`,
`implementation_authorization_stabilization_approval=false`,
`explicit_approval_record_approval=false`,
`explicit_approval_record_freeze_approval=false`,
`runtime_enablement_guard_release_approved=false`,
`runtime_approval_board_decision_approved=false`, `implementation_go_status=false`,
and `runtime_implementation_approved=false`. No v0.2 tag or release is created.

## AION-149 Implementation Authorization Final Review

AION-149 closes schema evidence without making an approval record effective.
`explicit_approval_record_approval=false`,
`explicit_approval_record_closeout_approval=false`, and
`implementation_authorization_final_review_approval=false`.
## AION-150 Authorization Track Closeout

AION-150 uses the explicit approval record schema in the master ledger without approving any record. Future implementation requires a separate explicit approval transaction using this schema.

The schema remains non-runtime with `explicit_approval_record_created=true`, `explicit_approval_record_approval=false`, `explicit_approval_record_freeze_approval=false`, `explicit_approval_record_closeout_approval=false`, and `implementation_go_status=false`.
