"""Operator integration with Contract Registry."""

from __future__ import annotations

from aion_brain.operator.action_center import ActionCenterService
from aion_brain.operator.queues import QueueSummaryBuilder
from tests.contract_registry_helpers import SCOPE, drift_finding, repository
from tests.operator_fakes import repository as operator_repository


def test_operator_action_center_surfaces_breaking_contract_findings() -> None:
    contract_repo = repository()
    contract_repo.save_finding(drift_finding())
    service = ActionCenterService(
        operator_repository(),
        contract_registry_repository=contract_repo,
    )

    items = service.build_action_items(SCOPE)

    assert any(item.source_type == "interface_drift" for item in items)


def test_operator_queue_summary_includes_contract_registry_queues() -> None:
    contract_repo = repository()
    contract_repo.save_finding(drift_finding())
    queues = QueueSummaryBuilder(contract_registry_repository=contract_repo).build_queues(SCOPE)

    assert any(
        queue.queue_type == "drift_findings" and queue.pending_count == 1 for queue in queues
    )
