# Release Transaction

The RC1 transaction starts only after the AION-244 evaluation and authorization PR merges with green CI.

Planned order:

1. Verify `main` contains the AION-244 authorization commits.
2. Verify `AION-244-V02REL-0001` is active and unconsumed.
3. Create annotated tag `aion-v0.2.0-rc.1` at `d35f1caa234d35dce1dfc0a80bc4c8e327a8373e`.
4. Create a draft GitHub prerelease named `AION OS v0.2.0-rc.1`.
5. Upload exactly 24 retained candidate assets.
6. Download and hash-verify all 24 assets.
7. Publish the prerelease and create the reconciliation PR.

No stable release or production deployment is part of this transaction.
