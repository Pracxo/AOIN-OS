from __future__ import annotations

import pytest
from pydantic import ValidationError

from aion_brain.contracts.counterfactuals import CounterfactualRunRequest


def test_counterfactual_run_request_rejects_empty_owner_scope() -> None:
    with pytest.raises(ValidationError):
        CounterfactualRunRequest(decision_frame_id="frame-1", owner_scope=[])
