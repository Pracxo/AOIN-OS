from __future__ import annotations

import pytest

from aion_brain.contracts.self_model import LimitationCreateRequest
from tests.self_model_helpers import DenyPolicy, bundle


def test_limitation_ledger_seeds_defaults_dry_run() -> None:
    services = bundle()

    result = services.limitations.seed_defaults(["workspace:main"], dry_run=True)

    assert result["dry_run"] is True
    assert result["created_count"] == 0
    assert any(
        item["limitation_key"] == "no_full_autonomy_default" for item in result["limitations"]
    )


def test_limitation_ledger_creates_limitation_through_policy() -> None:
    services = bundle()

    record = services.limitations.create_limitation(
        LimitationCreateRequest(
            limitation_key="generic.test_limit",
            category="generic",
            severity="critical",
            title="Generic test limitation",
            description="A deterministic test limitation.",
            owner_scope=["workspace:main"],
        )
    )

    assert record.status == "active"
    assert services.policy.requests[-1].action_type == "self_model.limitation.create"


def test_policy_deny_blocks_limitation_create() -> None:
    services = bundle(DenyPolicy())

    with pytest.raises(PermissionError):
        services.limitations.create_limitation(
            LimitationCreateRequest(
                limitation_key="generic.denied_limit",
                category="generic",
                severity="medium",
                title="Denied limitation",
                description="Policy denies this create.",
                owner_scope=["workspace:main"],
            )
        )
