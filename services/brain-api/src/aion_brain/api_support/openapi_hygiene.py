"""OpenAPI contract hygiene checks for AION Brain."""

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from aion_brain.contracts.api import OpenAPIHygieneReport

_PROVIDER_SCHEMA_MARKERS = (
    "OpenAI",
    "Anthropic",
    "Gemini",
    "LiteLLM",
    "Temporal",
    "Graphiti",
    "TurboVec",
    "MCP",
)
_DOMAIN_ROUTE_PREFIXES = (
    "/finance",
    "/trading",
    "/legal",
    "/healthcare",
    "/hr",
    "/procurement",
    "/it-automation",
)


class OpenAPIHygieneChecker:
    """Run deterministic checks over an OpenAPI schema."""

    def check(self, schema: dict[str, Any]) -> OpenAPIHygieneReport:
        """Return hygiene violations for a generated OpenAPI document."""
        paths = schema.get("paths", {})
        violations: list[dict[str, Any]] = []
        route_count = 0
        if isinstance(paths, dict):
            for path, operations in paths.items():
                route_count += self._check_path(str(path), operations, violations)
        self._check_schema_names(schema, violations)
        return OpenAPIHygieneReport(
            report_id=f"openapi-hygiene-{uuid4().hex}",
            status="failed" if violations else "passed",
            violations=violations,
            route_count=route_count,
            checked_at=datetime.now(UTC),
        )

    def _check_path(
        self,
        path: str,
        operations: Any,
        violations: list[dict[str, Any]],
    ) -> int:
        if "//" in path:
            violations.append({"path": path, "rule": "no_double_slashes"})
        if any(path.startswith(prefix) for prefix in _DOMAIN_ROUTE_PREFIXES):
            violations.append({"path": path, "rule": "no_domain_route_prefix"})
        if not isinstance(operations, dict):
            return 0
        count = 0
        for method, operation in operations.items():
            if str(method).lower() not in {
                "get",
                "put",
                "post",
                "delete",
                "patch",
                "options",
                "head",
            }:
                continue
            count += 1
            if not isinstance(operation, dict):
                continue
            if not operation.get("tags"):
                violations.append({"path": path, "method": method, "rule": "route_tags_required"})
            if not operation.get("operationId"):
                violations.append({"path": path, "method": method, "rule": "operation_id_required"})
        return count

    def _check_schema_names(
        self,
        schema: dict[str, Any],
        violations: list[dict[str, Any]],
    ) -> None:
        components = schema.get("components", {})
        schemas = components.get("schemas", {}) if isinstance(components, dict) else {}
        if not isinstance(schemas, dict):
            return
        for name in schemas:
            marker = next((item for item in _PROVIDER_SCHEMA_MARKERS if item in str(name)), None)
            if marker is not None and not _is_allowed_internal_marker(str(name), marker):
                violations.append(
                    {"schema": str(name), "marker": marker, "rule": "no_provider_schema_leakage"}
                )


def _missing_error_response(responses: dict[str, Any]) -> bool:
    return not any(code in responses for code in ("400", "401", "403", "404", "422", "500"))


def _is_allowed_internal_marker(name: str, marker: str) -> bool:
    if marker == "MCP":
        return "MCP" in name
    return any(
        allowed in name
        for allowed in (
            "AdapterStatus",
            "Compat",
            "ConfigStatus",
            "Episode",
            "IndexStatus",
            "ProviderHealth",
            "Reindex",
            "Rebuild",
            "Sync",
            "ModelProvider",
            "ModelProfile",
        )
    )
