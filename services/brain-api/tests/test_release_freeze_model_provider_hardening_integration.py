"""Release and freeze gate integration for provider hardening."""

from __future__ import annotations

from aion_brain.contracts.model_provider_hardening import ModelProviderBlocker
from tests.kernel_fakes import kernel_container
from tests.model_provider_hardening_helpers import repository


def test_freeze_gate_provider_hardening_check_warns_only_by_default() -> None:
    container = kernel_container()
    hardening_repo = repository()
    hardening_repo.save_blocker(
        ModelProviderBlocker(
            provider_blocker_id="blocker-1",
            provider_key="generic.metadata_only",
            blocker_type="raw_prompt_detected",
            severity="critical",
            status="open",
            reason="Unsafe prompt body metadata was detected.",
            recommended_action="review prompt egress preview",
        )
    )
    container.freeze_gate_service.set_model_provider_hardening_repository(hardening_repo)

    result = container.freeze_gate_service._check_model_provider_hardening_safe()  # noqa: SLF001

    assert result["status"] == "warning"
    assert result["details"]["provider_enabled"] is False


def test_release_package_includes_provider_hardening_summary_only() -> None:
    container = kernel_container()
    hardening_repo = repository()
    hardening_repo.save_blocker(
        ModelProviderBlocker(
            provider_blocker_id="blocker-1",
            provider_key="generic.metadata_only",
            blocker_type="raw_prompt_detected",
            severity="high",
            status="open",
            reason="Unsafe prompt body metadata was detected.",
            recommended_action="review prompt egress preview",
        )
    )
    container.release_packager.set_model_provider_hardening_repository(hardening_repo)

    summary = container.release_packager._model_provider_hardening_summary(  # noqa: SLF001
        ["workspace:main"]
    )

    assert summary["metadata_only"] is True
    assert summary["prompt_transmission_allowed"] is False
    assert summary["critical_blocker_count"] == 1
