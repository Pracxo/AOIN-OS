"""Static architecture boundary checks for AION Brain core."""

import ast
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from aion_brain.contracts.kernel import ArchitectureBoundaryReport

_ALLOWED_VENDOR_IMPORTS: dict[str, tuple[str, ...]] = {
    "langgraph": ("runtime/langgraph_runtime.py",),
    "turbovec": ("memory/turbovec_compat.py",),
    "graphiti": ("memory/graphiti_compat.py",),
    "litellm": ("reasoning/litellm_adapter.py",),
    "langfuse": ("observability/langfuse_adapter.py",),
    "minio": ("storage/minio_adapter.py",),
    "temporalio": ("workflows/temporal_compat.py",),
    "mcp": ("mcp/compat.py",),
    "docker": ("sandbox/docker_adapter.py",),
    "firecracker": ("sandbox/firecracker_adapter.py",),
    "openai": ("reasoning/providers/",),
    "anthropic": ("reasoning/providers/",),
    "google.generativeai": ("reasoning/providers/",),
}
_BANNED_IMPORTS = {"subprocess", "pty", "playwright", "selenium", "auth0", "okta"}
_BANNED_DOMAINS = {"finance", "trading", "legal", "healthcare", "hr", "procurement", "it"}
_BANNED_POLICY_PREFIXES = _BANNED_DOMAINS | {"medical"}


class ArchitectureBoundaryChecker:
    """Scan source files for direct vendor leakage and forbidden core behavior."""

    def __init__(self, source_root: str | Path) -> None:
        self._source_root = Path(source_root)

    def check(self) -> ArchitectureBoundaryReport:
        """Return a deterministic architecture boundary report."""
        violations: list[dict[str, object]] = []
        checked_paths: list[str] = []
        for directory in self._source_root.rglob("*"):
            if directory.is_dir() and directory.name.lower() in _BANNED_DOMAINS:
                violations.append(
                    {"type": "domain_directory", "path": str(directory), "name": directory.name}
                )
        for path in sorted(self._source_root.rglob("*.py")):
            relative = path.relative_to(self._source_root).as_posix()
            checked_paths.append(relative)
            try:
                tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            except SyntaxError as exc:
                violations.append({"type": "syntax_error", "path": relative, "line": exc.lineno})
                continue
            for node in ast.walk(tree):
                module = _import_module(node)
                if module is not None:
                    violations.extend(
                        self._import_violations(module, relative, getattr(node, "lineno", 0))
                    )
                if _raw_opa_http_usage(path, relative, node):
                    violations.append(
                        {
                            "type": "raw_opa_http_usage",
                            "path": relative,
                            "line": getattr(node, "lineno", 0),
                        }
                    )
                if _domain_policy_default(relative, node):
                    violations.append(
                        {
                            "type": "domain_policy_default",
                            "path": relative,
                            "line": getattr(node, "lineno", 0),
                        }
                    )
                if _is_os_system_call(node):
                    violations.append(
                        {
                            "type": "shell_execution",
                            "path": relative,
                            "line": getattr(node, "lineno", 0),
                        }
                    )
        return ArchitectureBoundaryReport(
            report_id=f"boundary-{uuid4().hex}",
            status="failed" if violations else "passed",
            violations=violations,
            checked_paths=checked_paths,
            created_at=datetime.now(UTC),
        )

    def _import_violations(
        self,
        module: str,
        relative: str,
        line: int,
    ) -> list[dict[str, object]]:
        root = module.split(".", 1)[0]
        if root in _BANNED_IMPORTS:
            return [{"type": "banned_import", "path": relative, "line": line, "module": module}]
        for vendor, allowed_paths in _ALLOWED_VENDOR_IMPORTS.items():
            if module == vendor or module.startswith(f"{vendor}."):
                if not any(relative.endswith(path) or path in relative for path in allowed_paths):
                    return [
                        {
                            "type": "vendor_import_outside_adapter",
                            "path": relative,
                            "line": line,
                            "module": module,
                        }
                    ]
        return []


def _import_module(node: ast.AST) -> str | None:
    if isinstance(node, ast.Import) and node.names:
        return node.names[0].name
    if isinstance(node, ast.ImportFrom):
        return node.module
    return None


def _is_os_system_call(node: ast.AST) -> bool:
    return (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "os"
        and node.func.attr == "system"
    )


def _domain_policy_default(relative: str, node: ast.AST) -> bool:
    if not relative.endswith("policy_catalog/defaults.py"):
        return False
    if not isinstance(node, ast.Constant) or not isinstance(node.value, str):
        return False
    value = node.value.lower()
    first_segment = value.split(".", 1)[0]
    return first_segment in _BANNED_POLICY_PREFIXES


def _raw_opa_http_usage(path: Path, relative: str, node: ast.AST) -> bool:
    if (
        relative.endswith("policy/opa_adapter.py")
        or relative.endswith("infra/opa.py")
        or relative.endswith("kernel/boundary_check.py")
        or "policy_catalog" in relative
    ):
        return False
    if not isinstance(node, ast.Constant) or not isinstance(node.value, str):
        return False
    value = node.value.lower()
    if "opa" not in value:
        return False
    try:
        source = path.read_text(encoding="utf-8").lower()
    except OSError:
        return False
    return "httpx" in source
