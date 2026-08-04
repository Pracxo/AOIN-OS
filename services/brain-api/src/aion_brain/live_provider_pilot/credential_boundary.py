"""Credential-boundary attestations for the AION-248 pilot."""

from __future__ import annotations

from datetime import datetime

from aion_brain.contracts.live_provider_pilot import LiveProviderCredentialBoundary


def attest_environment_credential(
    *,
    boundary_id: str,
    credential_present: bool,
    provider_credentials_read: int,
    created_at: datetime,
) -> LiveProviderCredentialBoundary:
    """Record presence/read counters without receiving the credential."""

    return LiveProviderCredentialBoundary(
        boundary_id=boundary_id,
        credential_present=credential_present,
        provider_credentials_read=provider_credentials_read,
        created_at=created_at,
    )


def reject_credential_file_input() -> None:
    """Credential files are outside AION-248 authorization."""

    raise ValueError("credential file input is rejected")


def reject_credential_cli_input() -> None:
    """Credential CLI arguments are outside AION-248 authorization."""

    raise ValueError("credential CLI input is rejected")
