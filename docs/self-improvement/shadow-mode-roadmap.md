# Shadow-Mode Roadmap

AION-177 authorized the AION-178 implementation task. AION-178 is now
implemented as disabled shadow-mode infrastructure:

- AION-178: controlled, observation-only contracts, reference adapter,
  pipeline, evidence, budget, redaction, replay, retention, output boundary, and
  operator review records are implemented.
- AION-179: formal closeout and read-only shadow-mode operator evaluation
  decision.

Out of scope until separate authorization:

- Runtime source rewrite.
- Runtime self-improvement activation.
- Git mutation.
- Pull request creation.
- Automatic merge.
- Production canary or deployment.
- Provider or connector calls.
- Model-weight training.
- v0.2 tag or release.

Exit criteria for AION-179 must include formal disposition of
`AION-177-SI-0006`, runtime-disabled checks, no-go regression checks, and
operator-visible evidence proving shadow mode remains advisory only.
