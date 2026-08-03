# AION-244 Operator Runbook

1. Confirm the evaluation and authorization PR is merged with green CI.
2. Sync `main` and rerun AION-244, AION-243, docs, boundary, and full repository checks.
3. Confirm `AION-244-V02REL-0001` is the only active v0.2 release qualification authorization.
4. Create annotated tag `aion-v0.2.0-rc.1` at `d35f1caa234d35dce1dfc0a80bc4c8e327a8373e`.
5. Create a draft GitHub prerelease named `AION OS v0.2.0-rc.1`.
6. Upload exactly the 24 inventory assets.
7. Download and verify all release assets before publishing.
8. Publish as prerelease, then reconcile through `phase/v02-rc1-publication-reconciliation`.

Do not create a stable v0.2 tag or release.
