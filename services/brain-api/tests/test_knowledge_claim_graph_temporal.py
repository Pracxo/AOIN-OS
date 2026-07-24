from __future__ import annotations

from test_knowledge_claim_graph_helpers import LATER, MUCH_LATER, NOW, valid_interval

from aion_brain.knowledge_intelligence.claim_graph_temporal import valid_time_intervals_overlap


def test_valid_time_overlap_respects_inclusive_boundaries_and_open_intervals() -> None:
    left = (valid_interval("left", start=NOW, end=LATER, end_inclusive=False),)
    touching = (valid_interval("right", start=LATER, end=MUCH_LATER, start_inclusive=True),)
    assert valid_time_intervals_overlap(left, touching) == "nonoverlap"
    open_left = (valid_interval("open-left", start=None, end=LATER),)
    assert valid_time_intervals_overlap(open_left, touching) == "overlap"
    assert valid_time_intervals_overlap((), touching) == "insufficient"
