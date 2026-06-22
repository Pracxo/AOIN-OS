from __future__ import annotations

from aion_brain.grounding.statement_splitter import StatementSplitter


def test_statement_splitter_splits_bullets_and_respects_limit() -> None:
    splitter = StatementSplitter()
    statements = splitter.split(
        "- First useful statement here.\n- Second useful statement here.",
        1,
    )
    assert statements == ["First useful statement here."]
