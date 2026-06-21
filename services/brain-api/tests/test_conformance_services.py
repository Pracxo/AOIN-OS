"""Conformance service and repository tests."""

from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from aion_brain.config import Settings
from aion_brain.conformance import (
    CapabilityTestVectorService,
    ConformanceFindingService,
    ConformanceProfileService,
    ConformanceQueryService,
    ConformanceRepository,
    ConformanceRunner,
    MockInvocationSimulator,
    ReadinessAssessmentService,
    SchemaConformanceChecker,
)
from aion_brain.contracts.conformance import (
    CapabilityTestVectorCreateRequest,
    ConformanceProfileCreateRequest,
    ConformanceQuery,
    ConformanceRunRequest,
)
from aion_brain.contracts.readiness import ReadinessAssessmentRequest
from tests.kernel_fakes import AllowPolicy, FakeTelemetry
from tests.module_binding_helpers import binding_request, module_binding_services, slot_request


def test_conformance_run_persists_mock_records_and_never_executes() -> None:
    services = _services()
    module_services = services["module_services"]
    slot = module_services["slot_service"].create_slot(slot_request())  # type: ignore[attr-defined]
    binding = module_services["binding_service"].create_binding(  # type: ignore[attr-defined]
        binding_request(
            slot.module_slot_id,
            requires_sandbox=False,
            input_schema={"type": "object", "required": ["text"]},
            output_schema={"type": "object", "properties": {"summary": {"type": "string"}}},
        )
    )
    vector = services["vectors"].create_vector(  # type: ignore[attr-defined]
        CapabilityTestVectorCreateRequest(
            capability_binding_id=binding.capability_binding_id,
            name="Generic vector",
            description="Metadata-only vector.",
            input_payload={"text": "hello"},
            expected_output_shape=binding.output_schema,
            owner_scope=["workspace:main"],
        )
    )

    run = services["runner"].run(  # type: ignore[attr-defined]
        ConformanceRunRequest(
            capability_binding_id=binding.capability_binding_id,
            test_vector_ids=[vector.test_vector_id],
            owner_scope=["workspace:main"],
        )
    )

    repository = services["repository"]
    mocks = repository.list_mock_invocations(  # type: ignore[attr-defined]
        capability_binding_id=binding.capability_binding_id
    )
    assert run.result["capability_executed"] is False
    assert run.result["extension_code_loaded"] is False
    assert run.result["source_records_mutated"] is False
    assert mocks and mocks[0].simulated_output["summary"] == "mock"


def test_readiness_blocks_when_required_conformance_is_missing() -> None:
    services = _services()
    assessment = services["readiness"].assess(  # type: ignore[attr-defined]
        ReadinessAssessmentRequest(
            capability_binding_id="binding-1",
            owner_scope=["workspace:main"],
        )
    )

    assert assessment.activation_ready is False
    assert assessment.status == "blocked"
    assert "missing_conformance_run" in assessment.blocker_refs


def test_conformance_query_returns_aggregate_records() -> None:
    services = _services()
    profile = services["profiles"].create_profile(  # type: ignore[attr-defined]
        ConformanceProfileCreateRequest(
            name="Generic profile",
            description="Metadata-only profile.",
            owner_scope=["workspace:main"],
        )
    )

    result = services["query"].query(ConformanceQuery(scope=["workspace:main"]))  # type: ignore[attr-defined]

    assert result.profiles[0].conformance_profile_id == profile.conformance_profile_id
    assert result.total_count >= 1
    assert "no_activation" in result.constraints


def _services() -> dict[str, object]:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    repository = ConformanceRepository(engine=engine)
    policy = AllowPolicy()
    telemetry = FakeTelemetry()
    settings = Settings(_env_file=None, DATABASE_URL="sqlite+pysqlite:///:memory:")
    module_services = module_binding_services(settings=settings)
    module_repository = module_services["repository"]
    schema_checker = SchemaConformanceChecker()
    mock_simulator = MockInvocationSimulator(
        repository,
        schema_checker=schema_checker,
        module_binding_repository=module_repository,  # type: ignore[arg-type]
        telemetry_service=telemetry,
        settings=settings,
    )
    return {
        "repository": repository,
        "settings": settings,
        "module_services": module_services,
        "profiles": ConformanceProfileService(
            repository,
            policy,
            telemetry_service=telemetry,
            settings=settings,
        ),
        "vectors": CapabilityTestVectorService(
            repository,
            policy,
            module_binding_repository=module_repository,  # type: ignore[arg-type]
            telemetry_service=telemetry,
            settings=settings,
        ),
        "runner": ConformanceRunner(
            repository,
            policy,
            schema_checker=schema_checker,
            mock_simulator=mock_simulator,
            module_binding_repository=module_repository,  # type: ignore[arg-type]
            settings=settings,
        ),
        "findings": ConformanceFindingService(repository, policy, telemetry_service=telemetry),
        "readiness": ReadinessAssessmentService(
            repository,
            policy,
            telemetry_service=telemetry,
            settings=settings,
        ),
        "query": ConformanceQueryService(repository, policy),
    }
