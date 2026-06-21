from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from aion_brain.contracts.compensation import CompensationPlan, CompensationStep
from aion_brain.contracts.run_control import RunControlRequest
from aion_brain.contracts.run_supervision import (
    RunStatusSample,
    RunSupervisionRecord,
    RunTimeoutPolicy,
)


def test_run_supervision_record_validates_target_system_and_scope() -> None:
    with pytest.raises(ValidationError):
        RunSupervisionRecord(
            run_supervision_id="run-1",
            source_type="generic",
            source_id="source-1",
            target_system="external",
            status="active",
            run_type="generic",
            owner_scope=["workspace:main"],
            title="Run",
            description="Run",
            current_status="unknown",
        )
    with pytest.raises(ValidationError):
        RunSupervisionRecord(
            run_supervision_id="run-1",
            source_type="generic",
            source_id="source-1",
            target_system="noop",
            status="active",
            run_type="generic",
            owner_scope=[],
            title="Run",
            description="Run",
            current_status="unknown",
        )


def test_sample_control_timeout_and_compensation_contracts_validate() -> None:
    with pytest.raises(ValidationError):
        RunStatusSample(
            run_status_sample_id="sample-1",
            run_supervision_id="run-1",
            target_system="noop",
            observed_status="completed",
            raw_status={"api_key": "secret"},
        )
    with pytest.raises(ValidationError):
        RunControlRequest(
            run_control_request_id="control-1",
            run_supervision_id="run-1",
            control_type="restart",
            status="requested",
            reason="check",
            requested_mode="dry_run",
            target_system="noop",
        )
    with pytest.raises(ValidationError):
        RunTimeoutPolicy(
            timeout_policy_id="policy-1",
            name="default",
            description="Default",
            status="active",
            target_system="noop",
            run_type="generic",
            timeout_seconds=0,
            stall_after_seconds=1,
            max_status_age_seconds=1,
            severity="medium",
            action_on_timeout="report_only",
            owner_scope=["workspace:main"],
        )
    with pytest.raises(ValidationError):
        CompensationPlan(
            compensation_plan_id="plan-1",
            source_type="generic",
            source_id="source-1",
            status="proposed",
            plan_type="domain_fix",
            title="Plan",
            description="Plan",
            owner_scope=["workspace:main"],
            trigger_reason="failed",
            risk_level="medium",
        )
    with pytest.raises(ValidationError):
        CompensationStep(
            compensation_step_id="step-1",
            compensation_plan_id="plan-1",
            step_order=0,
            step_type="inspect",
            status="proposed",
            title="Inspect",
            description="Inspect",
            risk_level="medium",
            created_at=datetime.now(UTC),
        )
