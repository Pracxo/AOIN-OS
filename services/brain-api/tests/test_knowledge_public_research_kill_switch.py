from __future__ import annotations

from public_research_pilot_test_helpers import make_envelope, make_plan

from aion_brain.knowledge_intelligence.public_research_pilot import ControlledPublicResearchPilot
from aion_brain.knowledge_intelligence.public_research_session import PublicResearchPilotKillSwitch


def test_kill_switch_blocks_candidate_creation() -> None:
    switch = PublicResearchPilotKillSwitch()
    switch.trigger("operator_requested_stop")
    result = ControlledPublicResearchPilot(
        clock=lambda: __import__("datetime").datetime(2026, 1, 1, tzinfo=__import__("datetime").UTC)
    ).run(envelope=make_envelope(), plans=(make_plan(),), kill_switch=switch)
    assert result.status == "killed"
    assert result.session.source_body_purged_count == 0
