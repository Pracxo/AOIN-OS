# AION-243 Release-Candidate Implementation

AION-243 implements the deterministic local release-candidate artifact-build
plane authorized by `AION-242-V02RQ-0003`.

The implementation adds strict Brain API contracts and an uninstalled local
runner. The contracts are pure validation models. The runner performs the local
artifact build from a clean immutable source commit and retains exactly one
bundle under the approved user-home policy.

The candidate is `aion-v0.2.0-rc.1`; Brain API and SDK package metadata move to
`0.2.0rc1` in the version-only commit. No production runtime, publication,
registry operation, package upload, Git tag or GitHub release is authorized.
