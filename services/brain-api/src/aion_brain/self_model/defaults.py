"""Default AION self-model records."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from aion_brain.contracts.self_model import LimitationCreateRequest, SelfModelProfile

AION_NAME = "AION"
AION_FULL_NAME = "Adaptive Intelligence Orchestration Nexus"
AION_OS_FULL_NAME = "Adaptive Intelligence Orchestration Nexus Operating System"

OPERATING_PRINCIPLES = [
    "Memory recall is not truth.",
    "Evidence grounds claims.",
    "Belief status and confidence are explicit.",
    "Decisions recommend but do not execute.",
    "Approvals do not auto-execute actions.",
    "Autonomy is constrained by operating mode.",
    "External tools and models are disabled by default.",
    "Domain modules plug in through governed contracts.",
    "No full autonomy is enabled by default.",
    "No chain-of-thought is stored.",
]

DEFAULT_LIMITATIONS: tuple[dict[str, Any], ...] = (
    {
        "limitation_key": "no_production_auth_v0_1",
        "category": "security",
        "severity": "critical",
        "title": "Production authentication is not enabled.",
        "description": "AION v0.1 uses local development identity boundaries by default.",
        "affected_capabilities": ["identity", "api"],
        "workaround": "Add production identity and authorization before shared deployment.",
    },
    {
        "limitation_key": "no_external_delivery_v0_1",
        "category": "external_integration",
        "severity": "high",
        "title": "External delivery is disabled.",
        "description": "AION v0.1 records local delivery only and does not send outbound messages.",
        "affected_capabilities": ["response", "connector"],
    },
    {
        "limitation_key": "no_cloud_deployment_v0_1",
        "category": "release",
        "severity": "medium",
        "title": "Cloud deployment is not part of v0.1.",
        "description": "AION v0.1 targets local development and release packaging.",
        "affected_capabilities": ["release"],
    },
    {
        "limitation_key": "no_untrusted_code_execution_v0_1",
        "category": "execution",
        "severity": "critical",
        "title": "Untrusted code execution is disabled.",
        "description": "Sandbox paths remain bounded and do not execute arbitrary untrusted code.",
        "affected_capabilities": ["sandbox", "execution"],
    },
    {
        "limitation_key": "no_full_autonomy_default",
        "category": "autonomy",
        "severity": "critical",
        "title": "Full autonomy is not enabled.",
        "description": "AION defaults to bounded modes and does not self-approve actions.",
        "affected_capabilities": ["autonomy", "approval", "execution"],
    },
    {
        "limitation_key": "optional_adapters_disabled_default",
        "category": "optional_adapter",
        "severity": "medium",
        "title": "Optional adapters are disabled unless configured.",
        "description": "External and specialized adapters remain optional.",
        "affected_capabilities": ["optional_adapter"],
    },
    {
        "limitation_key": "no_llm_claim_extraction_default",
        "category": "grounding",
        "severity": "medium",
        "title": "LLM claim extraction is not enabled by default.",
        "description": (
            "Claim extraction remains deterministic unless model gateway paths are configured."
        ),
        "affected_capabilities": ["belief", "reasoning"],
    },
    {
        "limitation_key": "no_domain_modules_in_core",
        "category": "generic",
        "severity": "medium",
        "title": "Domain modules are not part of Brain core.",
        "description": (
            "AION core exposes generic contracts and does not contain vertical workflows."
        ),
        "affected_capabilities": ["module", "capability"],
    },
    {
        "limitation_key": "no_raw_secret_storage",
        "category": "security",
        "severity": "critical",
        "title": "Raw secrets must not be stored.",
        "description": (
            "AION contracts reject secret-like keys and store references instead of raw secrets."
        ),
        "affected_capabilities": ["security", "audit"],
    },
    {
        "limitation_key": "restore_apply_disabled_default",
        "category": "resilience",
        "severity": "high",
        "title": "Restore apply is disabled by default.",
        "description": (
            "Backup restore defaults to preview behavior and requires explicit governance later."
        ),
        "affected_capabilities": ["backup", "resilience"],
    },
    {
        "limitation_key": "sandbox_execution_disabled_default",
        "category": "execution",
        "severity": "high",
        "title": "Sandbox execution is disabled by default.",
        "description": (
            "Sandbox services expose validation and controlled stubs before live execution."
        ),
        "affected_capabilities": ["sandbox", "execution"],
    },
    {
        "limitation_key": "external_model_calls_disabled_default",
        "category": "external_integration",
        "severity": "high",
        "title": "External model calls are disabled by default.",
        "description": (
            "AION v0.1 uses deterministic local paths unless model gateway settings change."
        ),
        "affected_capabilities": ["reasoning", "response"],
    },
)


def default_profile(settings: object, scope: list[str]) -> SelfModelProfile:
    """Return the built-in factual AION self-model profile."""
    now = datetime.now(UTC)
    version = str(
        getattr(settings, "aion_release_version", None)
        or getattr(settings, "version", None)
        or "0.1.0"
    )
    return SelfModelProfile(
        self_model_id="self-model-aion-default",
        name=AION_NAME,
        full_name=AION_FULL_NAME,
        version=version,
        status="active",
        description=(
            "AION is a modular AI Brain operating system for governed memory, reasoning, "
            "planning, policy, autonomy, workflows, tools, and future domain modules."
        ),
        operating_principles=OPERATING_PRINCIPLES,
        architecture_refs=[
            "docs/architecture.md",
            "docs/brain-contract.md",
            "docs/adr/0052-self-model-capability-awareness.md",
        ],
        owner_scope=scope,
        metadata={
            "official_os_name": AION_OS_FULL_NAME,
            "descriptive_only": True,
            "production_readiness_claim": False,
        },
        created_at=now,
        updated_at=now,
    )


def default_limitation_requests(scope: list[str]) -> list[LimitationCreateRequest]:
    """Return default limitation create requests."""
    return [
        LimitationCreateRequest(
            limitation_id=f"limitation-{item['limitation_key']}",
            owner_scope=scope,
            disclosure_required=True,
            metadata={"default": True, "default_id": uuid4().hex},
            **item,
        )
        for item in DEFAULT_LIMITATIONS
    ]
