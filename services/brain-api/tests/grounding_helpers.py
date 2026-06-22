from __future__ import annotations

from types import SimpleNamespace

from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from aion_brain.contracts.grounding import GroundingSource
from aion_brain.contracts.policy import PolicyDecision, PolicyRequest
from aion_brain.grounding.citation_mapper import CitationMapper
from aion_brain.grounding.citations import CitationService
from aion_brain.grounding.coverage import SourceCoverageService
from aion_brain.grounding.query import GroundingQueryService
from aion_brain.grounding.repository import GroundingRepository
from aion_brain.grounding.sources import GroundingSourceService
from aion_brain.grounding.statement_splitter import StatementSplitter
from aion_brain.grounding.support_checker import SupportChecker
from aion_brain.grounding.verifier import GroundingVerifier


class AllowPolicy:
    def authorize(self, request: PolicyRequest) -> PolicyDecision:
        return PolicyDecision(
            decision_id=f"decision-{request.request_id}",
            trace_id=request.trace_id or "",
            allow=True,
            approval_required=False,
            reason="allowed",
            constraints=[],
            audit_level="standard",
        )


class DenyPolicy:
    def authorize(self, request: PolicyRequest) -> PolicyDecision:
        return PolicyDecision(
            decision_id=f"decision-{request.request_id}",
            trace_id=request.trace_id or "",
            allow=False,
            approval_required=False,
            reason="denied",
            constraints=["test"],
            audit_level="high",
        )


class FakeTelemetry:
    def __init__(self) -> None:
        self.events: list[object] = []

    def emit(self, event: object) -> None:
        self.events.append(event)


class FakeAudit:
    def __init__(self) -> None:
        self.records: list[object] = []

    def record(self, request: object) -> object:
        entry = SimpleNamespace(
            audit_entry_id=f"audit-{len(self.records) + 1}",
            request=request,
        )
        self.records.append(entry)
        return entry


class FakeProvenance:
    def __init__(self) -> None:
        self.links: list[object] = []

    def create_link(self, link: object) -> object:
        self.links.append(link)
        return link


def repository() -> GroundingRepository:
    return GroundingRepository(
        engine=create_engine(
            "sqlite+pysqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
    )


def service_bundle(policy: object | None = None) -> SimpleNamespace:
    repo = repository()
    policy_adapter = policy or AllowPolicy()
    telemetry = FakeTelemetry()
    audit = FakeAudit()
    provenance = FakeProvenance()
    source_service = GroundingSourceService(
        repo,
        policy_adapter,
        telemetry_service=telemetry,
        audit_sink=audit,
    )
    citation_service = CitationService(
        repo,
        policy_adapter,
        telemetry_service=telemetry,
        audit_sink=audit,
        provenance_service=provenance,
    )
    splitter = StatementSplitter()
    checker = SupportChecker()
    mapper = CitationMapper(
        repo,
        policy_adapter,
        citation_service=citation_service,
        source_service=source_service,
        splitter=splitter,
        support_checker=checker,
        telemetry_service=telemetry,
        audit_sink=audit,
        provenance_service=provenance,
    )
    coverage = SourceCoverageService(
        repo,
        policy_adapter,
        telemetry_service=telemetry,
        audit_sink=audit,
    )
    verifier = GroundingVerifier(
        repo,
        policy_adapter,
        citation_mapper=mapper,
        coverage_service=coverage,
        source_service=source_service,
        telemetry_service=telemetry,
        audit_sink=audit,
        provenance_service=provenance,
    )
    query = GroundingQueryService(repo, policy_adapter)
    return SimpleNamespace(
        repository=repo,
        policy=policy_adapter,
        telemetry=telemetry,
        audit=audit,
        provenance=provenance,
        source_service=source_service,
        citation_service=citation_service,
        splitter=splitter,
        checker=checker,
        mapper=mapper,
        coverage=coverage,
        verifier=verifier,
        query=query,
    )


def source(summary: str = "AION records deterministic source support.") -> GroundingSource:
    return GroundingSource(
        grounding_source_id="grounding-source-1",
        trace_id="trace-1",
        source_type="evidence",
        source_id="evidence-1",
        title="Evidence",
        summary=summary,
        content_hash="hash-1",
        sensitivity="internal",
        trust_level="primary",
        evidence_refs=["evidence-1"],
        belief_refs=[],
        memory_refs=[],
        entity_refs=[],
        provenance_refs=[],
        owner_scope=["workspace:main"],
        metadata={},
        created_at=None,
        deleted_at=None,
    )
