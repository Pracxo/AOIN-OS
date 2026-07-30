from __future__ import annotations

from datetime import timedelta

import pytest
from pydantic import ValidationError

from tests.secure_runtime_test_support import make_authorization, make_signed_assertion


def test_authorization_envelope_is_exact_local_operator_authorization() -> None:
    from tests.secure_runtime_test_support import build_identity_pipeline

    _pipeline, signing_material = build_identity_pipeline()
    assertion = make_signed_assertion(signing_material)
    authorization = make_authorization(assertion)

    assert authorization.authorization_transaction_id == "AION-230-SRI-0001"
    assert authorization.implementation_task == "AION-231"
    assert authorization.operator_invoked is True
    assert authorization.local_session is True
    assert authorization.production_runtime is False
    assert authorization.network_access is False
    assert authorization.actual_execution is False


def test_authorization_rejects_production_or_long_lived_session() -> None:
    from tests.secure_runtime_test_support import build_identity_pipeline

    _pipeline, signing_material = build_identity_pipeline()
    assertion = make_signed_assertion(signing_material)
    payload = make_authorization(assertion).model_dump(mode="python")
    payload["production_runtime"] = True
    with pytest.raises(ValidationError):
        type(make_authorization(assertion))(**payload)
    payload = make_authorization(assertion).model_dump(mode="python")
    payload["expires_at"] = payload["created_at"] + timedelta(hours=2)
    with pytest.raises(ValidationError):
        type(make_authorization(assertion))(**payload)
