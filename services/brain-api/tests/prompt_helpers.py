"""Shared prompt governance test helpers."""

from __future__ import annotations

from types import SimpleNamespace

from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from aion_brain.contracts.policy import PolicyDecision, PolicyRequest
from aion_brain.contracts.prompts import PromptCompileRequest, PromptSection
from aion_brain.prompts.boundary import PromptBoundaryChecker
from aion_brain.prompts.compiler import PromptPacketCompiler
from aion_brain.prompts.manifest import ModelInputManifestService
from aion_brain.prompts.repository import PromptRepository
from aion_brain.prompts.sectioner import PromptSectioner


class AllowPolicy:
    """Policy fake that allows and records requests."""

    def __init__(self) -> None:
        self.requests: list[PolicyRequest] = []

    def authorize(self, request: PolicyRequest) -> PolicyDecision:
        self.requests.append(request)
        return PolicyDecision(
            decision_id=f"decision-{len(self.requests)}",
            trace_id=request.trace_id or "",
            allow=True,
            approval_required=False,
            reason="allowed",
            constraints=[],
            audit_level="standard",
        )


class DenyPolicy(AllowPolicy):
    """Policy fake that denies one action."""

    def __init__(self, action_type: str) -> None:
        super().__init__()
        self.action_type = action_type

    def authorize(self, request: PolicyRequest) -> PolicyDecision:
        self.requests.append(request)
        allow = request.action_type != self.action_type
        return PolicyDecision(
            decision_id=f"decision-{len(self.requests)}",
            trace_id=request.trace_id or "",
            allow=allow,
            approval_required=not allow,
            reason="allowed" if allow else "denied",
            constraints=[] if allow else ["blocked"],
            audit_level="standard" if allow else "high",
        )


class FakeTelemetry:
    """Collect emitted events."""

    def __init__(self) -> None:
        self.events: list[object] = []

    def emit(self, event: object) -> None:
        self.events.append(event)


def repository() -> PromptRepository:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    return PromptRepository(engine=engine)


def compiler(
    policy: AllowPolicy | None = None,
) -> tuple[PromptPacketCompiler, PromptRepository, AllowPolicy]:
    repo = repository()
    selected_policy = policy or AllowPolicy()
    telemetry = FakeTelemetry()
    boundary = PromptBoundaryChecker(repo, selected_policy, telemetry_service=telemetry)
    manifest = ModelInputManifestService(repo, selected_policy, telemetry_service=telemetry)
    return (
        PromptPacketCompiler(
            repo,
            selected_policy,
            sectioner=PromptSectioner(),
            boundary_checker=boundary,
            manifest_service=manifest,
            telemetry_service=telemetry,
            settings=SimpleNamespace(
                prompt_compiler_enabled=True,
                prompt_boundary_enabled=True,
                prompt_store_packets=True,
                prompt_injection_block_high_severity=True,
            ),
        ),
        repo,
        selected_policy,
    )


def safe_section() -> PromptSection:
    return PromptSection(
        section_id="section-1",
        section_type="retrieved_context",
        title="Context",
        content="AION has generic context.",
        priority=100,
        source_type="test",
        source_id="source-1",
        trust_level="retrieved_context",
        required=False,
        redacted=False,
    )


def compile_request(text: str = "answer generically") -> PromptCompileRequest:
    return PromptCompileRequest(
        trace_id="trace-1",
        packet_type="generic",
        owner_scope=["workspace:main"],
        user_message=text,
        sections=[safe_section()],
        metadata={"source": "test"},
    )
