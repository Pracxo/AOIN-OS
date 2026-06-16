from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from aion_brain.contracts.dialogue import DialogueMessage, DialogueSession, DialogueTurnRequest


def test_dialogue_session_validates_status_and_session_type() -> None:
    session = DialogueSession(
        dialogue_session_id="session-1",
        status="active",
        session_type="general",
        title="General",
        owner_scope=["workspace:main"],
    )

    assert session.status == "active"
    with pytest.raises(ValidationError):
        DialogueSession(
            dialogue_session_id="session-2",
            status="bad",
            session_type="general",
            title="General",
            owner_scope=["workspace:main"],
        )


def test_dialogue_session_rejects_empty_owner_scope() -> None:
    with pytest.raises(ValidationError):
        DialogueSession(
            dialogue_session_id="session-1",
            status="active",
            session_type="general",
            title="General",
            owner_scope=[],
        )


def test_dialogue_message_validates_role_and_message_type() -> None:
    message = DialogueMessage(
        message_id="message-1",
        dialogue_session_id="session-1",
        role="user",
        message_type="text",
        content="hello",
        content_hash="hash",
        content_redacted=False,
        created_at=datetime.now(UTC),
    )

    assert message.role == "user"
    with pytest.raises(ValidationError):
        DialogueMessage(
            message_id="message-2",
            dialogue_session_id="session-1",
            role="invalid",
            message_type="text",
            content="hello",
            content_hash="hash",
            content_redacted=False,
        )


def test_dialogue_message_rejects_chain_of_thought_content() -> None:
    with pytest.raises(ValidationError):
        DialogueMessage(
            message_id="message-1",
            dialogue_session_id="session-1",
            role="user",
            message_type="text",
            content="chain_of_thought: hidden",
            content_hash="hash",
            content_redacted=False,
        )


def test_dialogue_turn_request_rejects_controlled_mode() -> None:
    with pytest.raises(ValidationError):
        DialogueTurnRequest(
            message="hello",
            owner_scope=["workspace:main"],
            mode="controlled",
        )
