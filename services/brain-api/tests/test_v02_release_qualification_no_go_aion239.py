from __future__ import annotations

import ast
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
RUNTIME_ROOT = REPO_ROOT / "services/brain-api/src/aion_brain/v02_release_qualification"
CONTRACT = (
    REPO_ROOT
    / "services/brain-api/src/aion_brain/contracts/v02_release_qualification.py"
)

EXPECTED_SOURCE = {
    "__init__.py",
    "authorization.py",
    "gap_matrix.py",
    "production_auth_composition.py",
    "request_identity.py",
    "replay_provisioning.py",
    "identity_provider.py",
    "key_lifecycle.py",
    "protected_material.py",
    "credential_lifecycle.py",
    "token_lifecycle.py",
    "session_lifecycle.py",
    "deployment_manifest.py",
    "artifact_provenance.py",
    "rollback.py",
    "observability.py",
    "threat_model.py",
    "runtime_guard.py",
    "release_gate.py",
    "integrity.py",
    "evidence.py",
}
PROHIBITED_IMPORTS = {
    "aiohttp",
    "boto3",
    "docker",
    "google.cloud",
    "httpx",
    "kubernetes",
    "os.environ",
    "requests",
    "socket",
    "ssl",
    "subprocess",
    "terraform",
    "urllib" ".request",
}
PROHIBITED_CALLS = {
    "open",
    "exec",
    "eval",
}
PROHIBITED_ATTRS = {
    "write",
    "write_text",
    "write_bytes",
    "mkdir",
    "rename",
    "unlink",
}


def test_exact_runtime_source_scope_and_blocked_files_absent():
    assert {path.name for path in RUNTIME_ROOT.iterdir() if path.is_file()} == EXPECTED_SOURCE
    assert CONTRACT.is_file()
    for name in (
        "network.py",
        "live_identity_provider.py",
        "secret_store.py",
        "credential_store.py",
        "token_store.py",
        "live_replay_ledger.py",
        "database.py",
        "deployer.py",
        "kubernetes.py",
        "terraform.py",
        "container_registry.py",
        "production_observability_exporter.py",
        "release_publisher.py",
        "background_worker.py",
        "scheduler.py",
    ):
        assert not (RUNTIME_ROOT / name).exists()
    assert not (
        REPO_ROOT / "services/brain-api/src/aion_brain/api/v02_release_qualification.py"
    ).exists()


def test_runtime_source_ast_contains_no_live_operations_or_filesystem_writes():
    for path in [CONTRACT, *sorted(RUNTIME_ROOT.glob("*.py"))]:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert alias.name not in PROHIBITED_IMPORTS, (path, alias.name)
            if isinstance(node, ast.ImportFrom):
                module = node.module or ""
                assert module not in PROHIBITED_IMPORTS, (path, module)
            if isinstance(node, ast.Call):
                func = node.func
                if isinstance(func, ast.Name):
                    assert func.id not in PROHIBITED_CALLS, (path, func.id)
                if isinstance(func, ast.Attribute):
                    assert func.attr not in PROHIBITED_ATTRS, (path, func.attr)
            if isinstance(node, ast.Attribute):
                full = (
                    f"{node.value.id}.{node.attr}"
                    if isinstance(node.value, ast.Name)
                    else node.attr
                )
                assert full not in PROHIBITED_IMPORTS, (path, full)


def test_repository_does_not_add_release_or_deployment_surfaces():
    assert not (REPO_ROOT / ".github/workflows/v02-release.yml").exists()
    assert not (REPO_ROOT / "services/brain-api/src/aion_brain/api/v02_release.py").exists()
    assert not (REPO_ROOT / "v02_release_qualification/network.py").exists()
    assert not list(REPO_ROOT.glob("**/migrations/*v02*release*qualification*"))
    assert not list(REPO_ROOT.glob("**/*v0.2*release*candidate*artifact*"))
