from __future__ import annotations

from aion_brain.contracts.entities import EntityExtractMentionsRequest
from aion_brain.entities.mention_extractor import EntityMentionExtractor


def test_mention_extractor_finds_bracket_and_identifier_mentions() -> None:
    mentions = EntityMentionExtractor().extract(
        EntityExtractMentionsRequest(
            source_type="dialogue_message",
            source_id="message-1",
            text="Remember [[Test Reference]] and test.reference.",
            owner_scope=["workspace:main"],
        )
    )

    assert [mention.mention_text for mention in mentions][:2] == [
        "Test Reference",
        "test.reference",
    ]
    assert mentions[0].mention_type == "explicit"
