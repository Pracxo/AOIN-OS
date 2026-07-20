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

## AION-179 Roadmap Update

AION-179 has recorded the formal disposition: `AION-177-SI-0006` is consumed by
AION-178, closed by AION-179, expired, and non-reusable. The next possible step
is not implementation; it is a separate controlled activation authorization
review, if a human explicitly requests it.
## AION-180 Roadmap Update

AION-180 records `AION-180-SI-0007` as the sole active implementation authorization for AION-181. It authorizes construction of a disabled controlled shadow activation control plane only. It does not authorize activation, runtime enablement, source mutation, Git mutation, approval creation, merge, promotion, canary, deployment, model training, a v0.2 tag, or a v0.2 release.

AION-SOE-001 remains successful advisory evidence and is not an approval. `AION-177-SI-0006` remains closed, expired, and non-reusable.

The next implementation task is AION-181; AION-182 remains the formal evaluation closeout before any future activation authorization can be considered.
