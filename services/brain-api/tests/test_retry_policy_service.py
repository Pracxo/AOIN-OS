"""Retry policy service tests."""

from __future__ import annotations

import pytest

from aion_brain.api_support.errors import AIONPolicyDeniedException
from aion_brain.resilience.retry_policies import RetryPolicyService
from tests.resilience_fakes import AllowPolicy, DenyPolicy, repository, retry_policy


def test_retry_policy_create_list_delay_and_should_retry() -> None:
    policy = AllowPolicy()
    service = RetryPolicyService(repository(), policy)
    saved = service.create_policy(retry_policy())

    listed = service.list_policies(target_type="command")
    assert [item.retry_policy_id for item in listed] == [saved.retry_policy_id]
    assert service.compute_delay_ms(saved, 2) == 200
    assert service.should_retry(saved, "failed", 1) is True
    assert service.should_retry(saved, "blocked_by_policy", 1) is False
    assert [request.action_type for request in policy.requests] == [
        "resilience.retry_policy.create",
        "resilience.retry_policy.read",
    ]


def test_retry_policy_seed_defaults_dry_run_does_not_persist() -> None:
    repo = repository()
    service = RetryPolicyService(repo, AllowPolicy())

    result = service.seed_defaults(dry_run=True)

    assert result["dry_run"] is True
    assert result["policy_count"] >= 1
    assert repo.list_retry_policies() == []


def test_retry_policy_policy_deny_blocks_create() -> None:
    service = RetryPolicyService(repository(), DenyPolicy("resilience.retry_policy.create"))

    with pytest.raises(AIONPolicyDeniedException):
        service.create_policy(retry_policy())
