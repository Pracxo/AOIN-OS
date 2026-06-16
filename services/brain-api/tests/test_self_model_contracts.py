from __future__ import annotations

import pytest
from pydantic import ValidationError

from aion_brain.contracts.confidence import SelfAssessmentRequest
from aion_brain.contracts.self_model import LimitationRecord, SelfModelProfile
from aion_brain.self_model.defaults import default_limitation_requests, default_profile
from tests.self_model_helpers import settings


def test_self_model_profile_requires_official_aion_meaning() -> None:
    profile = default_profile(settings(), ["workspace:main"])

    assert profile.name == "AION"
    assert profile.full_name == "Adaptive Intelligence Orchestration Nexus"


def test_self_model_profile_rejects_sentience_claim() -> None:
    with pytest.raises(ValidationError):
        SelfModelProfile(
            self_model_id="self-1",
            name="AION",
            full_name="Adaptive Intelligence Orchestration Nexus",
            version="0.1.0",
            status="active",
            description="AION is sentient.",
            operating_principles=["Be factual."],
            owner_scope=["workspace:main"],
            metadata={},
        )


def test_self_model_profile_rejects_production_readiness_claim() -> None:
    with pytest.raises(ValidationError):
        SelfModelProfile(
            self_model_id="self-1",
            name="AION",
            full_name="Adaptive Intelligence Orchestration Nexus",
            version="0.1.0",
            status="active",
            description="AION is production ready.",
            operating_principles=["Be factual."],
            owner_scope=["workspace:main"],
            metadata={},
        )


def test_limitation_record_validates_key_and_defaults_include_no_full_autonomy() -> None:
    with pytest.raises(ValidationError):
        LimitationRecord(
            limitation_id="limitation-1",
            limitation_key="No.Full.Autonomy",
            category="autonomy",
            status="active",
            severity="critical",
            title="No full autonomy",
            description="Full autonomy is disabled.",
            disclosure_required=True,
            owner_scope=["workspace:main"],
            metadata={},
        )

    keys = {item.limitation_key for item in default_limitation_requests(["workspace:main"])}
    assert "no_full_autonomy_default" in keys


def test_self_assessment_request_rejects_empty_scope() -> None:
    with pytest.raises(ValidationError):
        SelfAssessmentRequest(owner_scope=[])
