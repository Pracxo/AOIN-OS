"""Policy authorization API."""

from functools import lru_cache
from typing import Annotated

from fastapi import APIRouter, Depends

from aion_brain.config import get_settings
from aion_brain.contracts.policy import PolicyDecision, PolicyRequest
from aion_brain.policy.base import PolicyAdapter
from aion_brain.policy.opa_adapter import OPAAdapter

router = APIRouter(prefix="/brain/policy", tags=["policy"])


def get_policy_adapter() -> PolicyAdapter:
    """Create the configured policy adapter."""
    return get_cached_policy_adapter(get_settings().opa_url)


@lru_cache
def get_cached_policy_adapter(opa_url: str) -> PolicyAdapter:
    """Return a cached OPA adapter for the configured OPA URL."""
    return OPAAdapter(opa_url)


@router.post("/authorize", response_model=PolicyDecision)
def authorize_policy(
    request: PolicyRequest,
    adapter: Annotated[PolicyAdapter, Depends(get_policy_adapter)],
) -> PolicyDecision:
    """Authorize a generic Brain action through the policy boundary."""
    return adapter.authorize(request)
