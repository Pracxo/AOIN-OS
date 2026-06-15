"""Model usage ledger tests."""

from datetime import UTC, datetime

from aion_brain.contracts.model_gateway import ModelUsageRecord
from aion_brain.model_gateway.usage import ModelUsageLedger
from tests.model_gateway_fakes import repository


def test_model_usage_ledger_records_and_lists_usage() -> None:
    ledger = ModelUsageLedger(repository())
    usage = ledger.record_usage(
        ModelUsageRecord(
            usage_id="usage-1",
            trace_id="trace-1",
            reasoning_id="reasoning-1",
            model_call_id="model-call-1",
            provider_id="deterministic",
            model_profile_id="aion-deterministic-v0",
            model_name="deterministic-reasoner-v0",
            mode="analyze",
            input_token_estimate=10,
            output_token_estimate=5,
            cost_estimate=0.0,
            latency_ms=0,
            status="recorded",
            actor_id="actor-1",
            workspace_id="workspace-1",
            created_at=datetime.now(UTC),
        )
    )
    records = ledger.list_usage(trace_id="trace-1")
    assert records == [usage]
