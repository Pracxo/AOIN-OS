"""Authorization helpers for the AION-228 continual-learning pilot."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import timedelta
from pathlib import Path

from aion_brain.contracts.governed_continual_learning import (
    AUTHORIZATION_TRANSACTION_ID,
    LIVE_CONFIRMATION_TEXT,
    ContinualLearningCyclePlan,
    ContinualLearningError,
    ContinualLearningPilotAuthorizationEnvelope,
    ContinualLearningPilotMode,
    build_record,
    continual_fingerprint,
    domain_allowlist_fingerprint,
    fingerprint_file_path,
    utc_now,
)
from aion_brain.knowledge_intelligence.public_research_policy import (
    canonicalize_public_research_url,
    normalize_domain_allowlist,
)


def live_confirmation_fingerprint() -> str:
    """Return the exact operator confirmation fingerprint for live mode."""

    return continual_fingerprint({"confirmation": LIVE_CONFIRMATION_TEXT})


def url_fingerprints(explicit_source_urls: Iterable[str]) -> tuple[str, ...]:
    """Fingerprint explicit public-research source URLs without retaining them."""

    return tuple(
        continual_fingerprint({"url": canonicalize_public_research_url(url)})
        for url in explicit_source_urls
    )


def claim_fingerprints(claims: Iterable[str]) -> tuple[str, ...]:
    """Fingerprint explicit claims without storing raw claim text in committed evidence."""

    return tuple(continual_fingerprint({"claim": claim}) for claim in claims)


def build_continual_learning_authorization_envelope(
    *,
    session_id: str,
    mode: ContinualLearningPilotMode,
    cycle_plans: tuple[ContinualLearningCyclePlan, ...],
    exact_domain_allowlist: tuple[str, ...],
    explicit_source_urls: tuple[str, ...],
    research_claims: tuple[str, ...],
    temporary_root: Path,
    temporary_store_path: Path,
    operator_identity_fingerprint: str,
) -> ContinualLearningPilotAuthorizationEnvelope:
    """Build the active AION-227-GLM-0004 envelope for one pilot session."""

    normalized_domains = normalize_domain_allowlist(exact_domain_allowlist)
    created_at = utc_now()
    return build_record(
        ContinualLearningPilotAuthorizationEnvelope,
        {
            "schema_version": "aion-glm-continual-learning-authorization/v1",
            "authorization_transaction_id": AUTHORIZATION_TRANSACTION_ID,
            "approval_record_id": AUTHORIZATION_TRANSACTION_ID,
            "session_id": session_id,
            "operator_identity_fingerprint": operator_identity_fingerprint,
            "mode": mode,
            "cycle_ids": tuple(plan.cycle_id for plan in cycle_plans),
            "cycle_plan_fingerprints": tuple(plan.cycle_plan_fingerprint for plan in cycle_plans),
            "exact_domain_allowlist": normalized_domains,
            "domain_allowlist_fingerprint": domain_allowlist_fingerprint(normalized_domains),
            "explicit_source_url_fingerprints": url_fingerprints(explicit_source_urls),
            "research_claim_fingerprints": claim_fingerprints(research_claims),
            "temporary_root_fingerprint": fingerprint_file_path(temporary_root),
            "temporary_store_path_fingerprint": fingerprint_file_path(temporary_store_path),
            "maximum_cycles": 3,
            "maximum_session_seconds": 7200,
            "created_at": created_at,
            "expires_at": created_at + timedelta(hours=2),
            "confirmation_fingerprint": (
                live_confirmation_fingerprint()
                if mode is ContinualLearningPilotMode.OPERATOR_INVOKED_LIVE
                else continual_fingerprint({"confirmation": "deterministic-simulation"})
            ),
        },
        "authorization_envelope_fingerprint",
    )


def validate_authorization(
    envelope: ContinualLearningPilotAuthorizationEnvelope,
    *,
    session_id: str | None = None,
    mode: ContinualLearningPilotMode | None = None,
) -> ContinualLearningPilotAuthorizationEnvelope:
    """Validate the current authorization envelope and fail closed on drift."""

    if envelope.authorization_transaction_id != AUTHORIZATION_TRANSACTION_ID:
        raise ContinualLearningError("unexpected continual-learning authorization")
    if envelope.approval_record_id != AUTHORIZATION_TRANSACTION_ID:
        raise ContinualLearningError("unexpected continual-learning approval record")
    if session_id is not None and envelope.session_id != session_id:
        raise ContinualLearningError("authorization envelope session mismatch")
    if mode is not None and envelope.mode is not mode:
        raise ContinualLearningError("authorization envelope mode mismatch")
    if envelope.maximum_cycles != 3:
        raise ContinualLearningError("authorization envelope must allow exactly three cycles")
    return envelope
