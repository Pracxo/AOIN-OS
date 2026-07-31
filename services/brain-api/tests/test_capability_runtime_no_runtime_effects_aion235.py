from __future__ import annotations

import ast

from capability_runtime_test_support import REPO_ROOT

RUNTIME_SOURCE = [
    "services/brain-api/src/aion_brain/contracts/sandboxed_capability_runtime.py",
    "services/brain-api/src/aion_brain/capability_runtime/__init__.py",
    "services/brain-api/src/aion_brain/capability_runtime/authorization.py",
    "services/brain-api/src/aion_brain/capability_runtime/component_binding.py",
    "services/brain-api/src/aion_brain/capability_runtime/manifests.py",
    "services/brain-api/src/aion_brain/capability_runtime/request_envelope.py",
    "services/brain-api/src/aion_brain/capability_runtime/input_validation.py",
    "services/brain-api/src/aion_brain/capability_runtime/execution_plan.py",
    "services/brain-api/src/aion_brain/capability_runtime/sandbox.py",
    "services/brain-api/src/aion_brain/capability_runtime/guard.py",
    "services/brain-api/src/aion_brain/capability_runtime/dispatcher.py",
    "services/brain-api/src/aion_brain/capability_runtime/reference_capabilities.py",
    "services/brain-api/src/aion_brain/capability_runtime/reference_connector.py",
    "services/brain-api/src/aion_brain/capability_runtime/budget.py",
    "services/brain-api/src/aion_brain/capability_runtime/audit.py",
    "services/brain-api/src/aion_brain/capability_runtime/observability.py",
    "services/brain-api/src/aion_brain/capability_runtime/integrity.py",
    "services/brain-api/src/aion_brain/capability_runtime/evidence.py",
]


def test_aion235_runtime_source_uses_no_prohibited_imports_or_calls() -> None:
    prohibited_import_roots = {
        "aiohttp",
        "httpx",
        "importlib",
        "os",
        "pathlib",
        "playwright",
        "requests",
        "selenium",
        "shutil",
        "socket",
        "ssl",
        "subprocess",
        "tempfile",
        "urllib",
    }
    prohibited_calls = {"open", "eval", "exec", "__import__"}
    for relative in RUNTIME_SOURCE:
        tree = ast.parse((REPO_ROOT / relative).read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert alias.name.split(".", 1)[0] not in prohibited_import_roots
            elif isinstance(node, ast.ImportFrom):
                assert (node.module or "").split(".", 1)[0] not in prohibited_import_roots
            elif isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    assert node.func.id not in prohibited_calls
                elif isinstance(node.func, ast.Attribute):
                    assert node.func.attr not in prohibited_calls
