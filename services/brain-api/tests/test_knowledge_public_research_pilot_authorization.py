from __future__ import annotations

from public_research_pilot_test_helpers import make_envelope, make_plan

from aion_brain.contracts.knowledge_public_research_pilot import PublicResearchPilotMode
from aion_brain.knowledge_intelligence.public_research_pilot import ControlledPublicResearchPilot


def test_authorization_envelope_controls_live_flag() -> None:
    envelope = make_envelope()
    assert envelope.authorization_transaction_id == "AION-218-KI-0008"
    assert envelope.live_network_access_approved is False


def test_live_plan_requires_live_authorization() -> None:
    plan = make_plan(mode=PublicResearchPilotMode.OPERATOR_INVOKED_LIVE)
    result = ControlledPublicResearchPilot().run(envelope=make_envelope(), plans=(plan,))
    assert result.status == "blocked"
