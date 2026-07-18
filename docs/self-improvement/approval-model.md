# Self-Improvement Approval Model

Task: AION-165

## Approval Binding

Self-improvement approval is always human-gated. Approval must bind to the exact proposal ID, exact candidate commit SHA, exact diff hash, exact benchmark fingerprint, exact rollback plan, and exact deployment or simulation scope.

Approval is invalidated by any post-approval source change, benchmark change, protected-core change outside its own elevated proposal, or mismatch between the approved commit and the pull request head.

## Separation Of Duties

The proposal author cannot approve the same proposal. AION cannot approve its own source changes. Protected-core proposals require dual approval and security review. Ordinary proposals cannot modify approval logic, no-go checks, release controls, policy controls, audit controls, or hidden holdout material.

## Merge Control

Merge is allowed only after human approval, exact commit and diff-hash matching, green GitHub checks, benchmark evidence unchanged, rollback metadata present, and branch protection satisfied. AION may never push directly to `main`.

## Default States

- `human_approval_required=true`
- `exact_commit_approval_required=true`
- `exact_diff_hash_approval_required=true`
- `no_self_approval=true`
- `automatic_merge_enabled=false`
