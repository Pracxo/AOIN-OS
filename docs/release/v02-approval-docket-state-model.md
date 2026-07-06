# v0.2 Approval Docket State Model

The approval docket state model defines preview-only states for future implementation decision records. No state approves implementation or enables runtime.

| State | Meaning | Approval effect | Runtime effect |
| --- | --- | --- | --- |
| `drafted` | Candidate record is drafted. | none | none |
| `docketed` | Candidate is listed in the docket. | none | none |
| `evidence_attached` | Required evidence is attached. | none | none |
| `decision_record_attached` | Implementation decision record is attached. | none | none |
| `review_ready_preview` | Review packet is complete enough for preview. | none | none |
| `runtime_review_pending` | Runtime approval review has not happened. | none | none |
| `blocked` | Required evidence or dependency is missing. | none | none |
| `rejected` | Candidate is rejected for the current lane. | none | none |
| `expired` | Candidate evidence is stale. | none | none |
| `revoked` | Candidate record is revoked. | none | none |
| `docket_unapproved` | Docket item is explicitly unapproved. | none | none |
| `implementation_unapproved` | Implementation remains explicitly unapproved. | none | none |

`approval_docket_item_approved=false`, `implementation_decision_record_approval=false`, `runtime_approval_review_approved=false`, `runtime_decision_lock_release_approved=false`, `runtime_decision_readiness_approved=false`, and `runtime_implementation_approved=false` in every state.
