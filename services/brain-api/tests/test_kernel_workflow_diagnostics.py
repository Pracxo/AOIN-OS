"""Kernel workflow diagnostics tests."""

from types import SimpleNamespace

from aion_brain.kernel.diagnostics import KernelDiagnostics


def test_kernel_diagnostics_include_workflow_readiness_checks() -> None:
    """Diagnostics expose workflow services and disabled-by-default worker state."""
    settings = SimpleNamespace(
        database_url="sqlite+pysqlite:///:memory:",
        redis_url="redis://localhost:6379/0",
        nats_url="nats://localhost:4222",
        opa_url="http://opa:8181",
        model_gateway_enabled=False,
        workflow_engine_adapter="local",
        workflow_local_worker_enabled=False,
        workflow_scheduler_enabled=False,
        temporal_enabled=False,
    )
    container = SimpleNamespace(
        settings=settings,
        adapter_config=SimpleNamespace(model_dump=lambda: {"workflow_engine_adapter": "local"}),
        policy_adapter=object(),
        memory_service=object(),
        semantic_memory_adapter=object(),
        graph_memory_adapter=object(),
        reasoning_mesh=object(),
        execution_orchestrator=object(),
        retrieval_router=object(),
        model_gateway_service=object(),
        prompt_redactor=object(),
        model_budget_guard=object(),
        visual_projection_service=object(),
        replay_service=object(),
        workflow_service=object(),
        local_workflow_engine=object(),
        workflow_scheduler=object(),
        workflow_worker=object(),
        temporal_adapter=SimpleNamespace(
            temporal_status=lambda: SimpleNamespace(package_available=False)
        ),
    )

    checks = KernelDiagnostics(container).run()
    by_name = {check.name: check for check in checks}

    assert by_name["workflow_service_present"].status == "passed"
    assert by_name["workflow_local_worker_disabled_by_default"].status == "passed"
    assert by_name["workflow_no_auto_background_loop"].status == "passed"
