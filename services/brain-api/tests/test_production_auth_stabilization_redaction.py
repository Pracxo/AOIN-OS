from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from aion_brain.contracts.production_auth import (
    ProductionAuthCoreConfig,
    ProductionAuthDiagnosticSnapshot,
    ProductionAuthPolicyRequest,
    ProductionAuthProvenanceRecord,
)


@pytest.mark.parametrize(
    "metadata",
    [
        {"nested": {"password": "blocked"}},
        {"items": [{"Credential": "blocked"}]},
        {"items": ({"client-secret": "blocked"},)},
        {"ACCESS-TOKEN": "blocked"},
        {"ｐassword": "blocked"},
        {"note": "contains access token"},
        {"exception_text": "provider payload leaked"},
        {"source_reference": "raw prompt echo"},
    ],
)
def test_redaction_rejects_protected_material_in_nested_metadata(
    metadata: dict[str, object],
) -> None:
    with pytest.raises(ValidationError):
        ProductionAuthPolicyRequest(
            request_id="request-redaction",
            requested_operation="core_status_read",
            metadata=metadata,
        )


@pytest.mark.parametrize(
    "value",
    [
        "refresh token",
        "ID token",
        "session token",
        "authorization header",
        "private key",
        "client secret",
        "raw identity claim",
        "hidden reasoning",
    ],
)
def test_diagnostics_reject_protected_material_values(value: str) -> None:
    with pytest.raises(ValidationError):
        ProductionAuthDiagnosticSnapshot(
            snapshot_id="snapshot-redaction",
            blocker_count=1,
            reason_codes=["production_auth_runtime_disabled"],
            metadata={"safe_key": f"contains {value}"},
            created_at=datetime(2026, 7, 13, tzinfo=UTC),
        )


def test_source_refs_reject_protected_material() -> None:
    with pytest.raises(ValidationError):
        ProductionAuthProvenanceRecord(
            provenance_id="prov-redaction",
            source_refs=("docs/private key/source.md",),
            created_at=datetime(2026, 7, 13, tzinfo=UTC),
        )


def test_config_metadata_rejects_raw_provider_payloads() -> None:
    with pytest.raises(ValidationError):
        ProductionAuthCoreConfig(metadata={"provider-payload": {"sub": "demo"}})
