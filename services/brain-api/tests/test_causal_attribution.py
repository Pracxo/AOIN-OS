from __future__ import annotations

from aion_brain.contracts.outcomes import CausalAttribution
from tests.outcome_helpers import bundle


def test_causal_attribution_service_creates_provenance_link() -> None:
    env = bundle()
    attribution = env.attribution.create_attribution(
        CausalAttribution(
            causal_attribution_id="cause-1",
            outcome_id="outcome-1",
            cause_type="command",
            cause_id="command-1",
            effect_type="observed_effect",
            effect_id="observed-1",
            relation_type="caused",
            confidence=0.8,
            evidence_refs=["evidence-1"],
            reasoning="The command record and evidence support this attribution.",
            metadata={},
        )
    )

    assert attribution.causal_attribution_id == "cause-1"
    assert env.provenance.links
