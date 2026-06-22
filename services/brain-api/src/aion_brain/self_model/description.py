"""Self-description facade."""

from __future__ import annotations

from typing import Any, cast

from aion_brain.contracts.self_model import SelfDescription, SelfDescriptionRequest


class SelfDescriptionService:
    """Thin facade used by APIs, SDKs, and dialogue integration."""

    def __init__(self, profile_service: Any) -> None:
        self._profile_service = profile_service

    def describe(self, request: SelfDescriptionRequest) -> SelfDescription:
        return cast(SelfDescription, self._profile_service.describe(request))
