from __future__ import annotations

import pytest
from public_research_pilot_test_helpers import make_plan

from aion_brain.contracts.knowledge_public_research_pilot import validate_domain_name


def test_plan_requires_exact_allowlist() -> None:
    plan = make_plan()
    assert plan.explicit_domain_allowlist == ("example.com",)
    with pytest.raises(ValueError):
        validate_domain_name("*.example.com")
