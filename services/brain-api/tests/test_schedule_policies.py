"""Schedule policy service tests."""

from __future__ import annotations

from aion_brain.contracts.scheduler import SchedulePolicy
from tests.scheduler_fakes import service_graph


def test_schedule_policy_create_and_list() -> None:
    _, _, _, _, _, policies, *_ = service_graph()
    policy = policies.create_policy(
        SchedulePolicy(
            policy_id="policy-1",
            policy_type="max_frequency",
            name="Max frequency",
            description="Report local frequency violations.",
            owner_scope=["workspace:main"],
            conditions={"max_per_hour": 10},
        )
    )

    assert policy.policy_id == "policy-1"
    assert policies.list_policies(["workspace:main"]) == [policy]
