from __future__ import annotations

import pytest
from pydantic import ValidationError

from tests.test_identity_assertion_contracts import make_payload


@pytest.mark.parametrize(
    "field",
    ["roles", "permissions", "security_scope"],
)
def test_duplicate_claims_fail(field: str) -> None:
    with pytest.raises(ValidationError):
        make_payload(**{field: ("one", "one")})


def test_claims_are_sorted_after_duplicate_check() -> None:
    payload = make_payload(
        roles=("viewer", "operator"),
        permissions=("read:z", "read:a"),
        security_scope=("scope:z", "scope:a"),
    )
    assert payload.roles == ("operator", "viewer")
    assert payload.permissions == ("read:a", "read:z")
    assert payload.security_scope == ("scope:a", "scope:z")


def test_claim_limits_enforced() -> None:
    with pytest.raises(ValidationError):
        make_payload(roles=tuple(f"role-{index}" for index in range(65)))
    with pytest.raises(ValidationError):
        make_payload(permissions=tuple(f"perm-{index}" for index in range(129)))
    with pytest.raises(ValidationError):
        make_payload(security_scope=tuple(f"scope-{index}" for index in range(129)))


def test_metadata_size_limit_enforced() -> None:
    with pytest.raises(ValidationError):
        make_payload(metadata={"large": "x" * 5000})
