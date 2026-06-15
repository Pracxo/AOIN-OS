"""Secret reference service tests."""

import pytest

from tests.sandbox_fakes import make_secret_service, secret_request


def test_secret_ref_service_creates_metadata_only_secret_ref() -> None:
    service = make_secret_service()

    secret_ref = service.create_secret_ref(secret_request())

    assert secret_ref.secret_ref_id == "secret-ref-1"
    assert secret_ref.external_ref == "env:AION_GENERIC_REF"


def test_secret_ref_service_refuses_raw_secret_values() -> None:
    service = make_secret_service()

    with pytest.raises(ValueError):
        service.rotate_metadata("secret-ref-1", "dev", {"token": "not-allowed"})
