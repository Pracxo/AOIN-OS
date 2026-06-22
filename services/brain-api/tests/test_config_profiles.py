"""Config profile service tests."""

from __future__ import annotations

import pytest

from aion_brain.api_support.errors import AIONPolicyDeniedException
from aion_brain.contracts.runtime_config import ConfigProfileCreateRequest
from tests.runtime_config_fakes import SCOPE, DenyPolicy, services


def test_config_profile_service_creates_profile_through_policy() -> None:
    _, profiles, *_ = services()

    profile = profiles.create_profile(
        ConfigProfileCreateRequest(
            name="local",
            description="local safe profile",
            owner_scope=SCOPE,
        )
    )

    assert profile.status == "active"
    assert profile.name == "local"


def test_policy_deny_blocks_profile_creation() -> None:
    _, profiles, *_ = services(policy=DenyPolicy())

    with pytest.raises(AIONPolicyDeniedException):
        profiles.create_profile(
            ConfigProfileCreateRequest(
                name="blocked",
                description="blocked profile",
                owner_scope=SCOPE,
            )
        )
