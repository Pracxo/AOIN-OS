# Architecture Roadmap

Task: `AION-238`.

Purpose: defines the AION-239 through AION-244 qualification roadmap without runtime activation.

## Post-RC1 Current Projection

Current released prerelease: `aion-v0.2.0-rc.1`.

Current development line: `v0.3`.

Current development version: `0.3.0.dev0`.

Current programme: `AION-ADAPTIVE-INTELLIGENCE-001`.

Current task: `AION-246`.

Current authorization: `AION-245-AI-0001`.

The v0.2 Release Qualification Program is complete. The RC1 prerelease is published with 24 assets, while stable v0.2.0 remains unpublished. The next programme is Adaptive Intelligence, with only AION-246 authorized.

Final evaluation: `AION-SRIPE-004`.

Decision: `CONTROLLED_OPERATOR_CONSOLE_INTEGRATED_LOCAL_RUNTIME_FINAL_EVALUATION_PASS_COMPLETE_SECURE_RUNTIME_INTEGRATION_PROGRAM_RECOMMEND_V02_RELEASE_QUALIFICATION_PROGRAM_AUTHORIZATION`.

Evidence fingerprint: `6e457d1a8bc226aa44697802d68b5d4cd5a272088a5ce6317048ab75503744ee`.

Result:

- `AION-236-SRI-0004` is closed, consumed by `AION-237`, expired, and non-reusable.
- `AION-SECURE-RUNTIME-INTEGRATION-001` is complete.
- Active Secure Runtime Integration implementation authorization count is `0`.
- `AION-V02-RELEASE-QUALIFICATION-001` is authorized but not implemented.
- `AION-238-V02RQ-0001` is the sole active authorization for `AION-239`.
- `AION-240` is the formal closeout task for `AION-239`.

Runtime and release boundary:

- Production runtime remains disabled.
- Public listeners remain disabled.
- External egress, DNS, providers, connectors and real tools remain disabled.
- Credentials, secrets, tokens, cookies and browser persistence remain absent.
- Historical marker: `v02_release_ready=false` at AION-238 programme authorization time.
- Historical marker: no v0.2 tag or release was approved or created at AION-238 programme authorization time.

## AION-239 Implemented Disabled Foundation

AION-239 implements the AION-238-authorized disabled v0.2 production-readiness qualification foundation. The foundation represents production-readiness gaps, production-auth composition, verified RequestIdentity integration, replay provisioning, IdP adapter contracts, key and protected-material policy, credential/token/session lifecycle, artifact/SBOM/provenance/reproducibility, rollback, observability, health, threat-model, release-gate and staging-plan evidence as strict local contracts.

The implementation is disabled and design-only. It performs no external identity-provider call, DNS lookup, credential generation, token issuance, replay-ledger write, database provisioning, staging or production deployment, rollback execution, observability export, release-candidate creation, tag creation or release publication. The deterministic pilot returns a release hold because staging and production evidence remain absent. AION-238-V02RQ-0001 remains active pending AION-240 closeout.

## AION-240 Foundation Evaluation And Staging Authorization

AION-240 records the immutable operator evaluation `AION-V02RQPE-001` for the merged AION-239 disabled v0.2 production-readiness qualification foundation.

Decision: `DISABLED_V02_PRODUCTION_READINESS_QUALIFICATION_FOUNDATION_OPERATOR_EVALUATION_PASS_RECOMMEND_CONTROLLED_ISOLATED_STAGING_ARTIFACT_AND_ROLLBACK_DRILL_QUALIFICATION_AUTHORIZATION`.

The evaluation passed all 28 hard-gated scenarios, verified PR #158, commits `a1d5d1ee2b0d991f3074c796d664105225b51856` and `fa789d5c43709d606bb088a69451b7a43cf32a17`, merge commit `154d58f182871ce18abad860f3bb76e5a006ebad`, the AION-239 pilot fingerprint `6635d4d32533893e4549d3992c0a6b54e73a58a0904914da6defcc5e0deff2ab`, twenty readiness domains, twenty readiness gaps, twenty-four release gates, forty threat scenarios and zero prohibited operational effects.

Historical marker: `AION-238-V02RQ-0001` is closed, consumed by AION-239, expired and non-reusable. `AION-240-V02RQ-0002` remained active for AION-241 formal closeout by AION-242. AION-241 was implemented with controlled isolated local pilot evidence pending AION-242 closeout. AION-243 was unauthorized. AION-244 was the final release-candidate evaluation and tag/release authorization decision.

Historical marker: production runtime, production authentication, external IdP calls, production credentials, production tokens, registry login, registry pull, registry push, public network access, DNS resolution, public listeners, production database provisioning, production deployment, release-candidate creation, v0.2 tags and v0.2 releases remained disabled or absent at that stage. Stable v0.2.0 remains unpublished after RC1.

## AION-244 v0.2.0-rc.1 Publication Authorization

AION-244 moves the v0.2 release qualification roadmap to final RC1 publication authorization. The only allowed publication target is the prerelease `aion-v0.2.0-rc.1` at `d35f1caa234d35dce1dfc0a80bc4c8e327a8373e`; stable v0.2.0 remains a future, separately evaluated release path.
