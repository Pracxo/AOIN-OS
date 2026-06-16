"""Local API exposure checker."""

from __future__ import annotations

import json
from typing import Any

FORBIDDEN_ROUTE_TERMS = (
    "finance",
    "trading",
    "legal",
    "healthcare",
    "medical",
    "payments",
    "procurement",
)
FORBIDDEN_ROUTE_PREFIXES = tuple(f"/{term}" for term in FORBIDDEN_ROUTE_TERMS if term != "payments")
PROVIDER_OBJECT_TERMS = (
    "openaiobject",
    "anthropicmessage",
    "litellmresponse",
    "sdk_response",
    "provider_response",
)


class APIExposureChecker:
    """Inspect FastAPI/OpenAPI metadata for unsafe exposure."""

    def check(self, openapi: dict[str, Any]) -> list[dict[str, Any]]:
        """Return exposure checks for one OpenAPI document."""
        paths = openapi.get("paths", {})
        route_paths = [str(path) for path in paths if isinstance(path, str)]
        serialized = json.dumps(openapi, sort_keys=True).lower()
        domain_routes = [
            path
            for path in route_paths
            if any(path.lower().startswith(prefix) for prefix in FORBIDDEN_ROUTE_PREFIXES)
            or any(term in path.lower() for term in FORBIDDEN_ROUTE_TERMS)
        ]
        stacktrace_routes = [
            path
            for path, methods in paths.items()
            if "stacktrace" in json.dumps(methods, sort_keys=True).lower()
            or "traceback" in json.dumps(methods, sort_keys=True).lower()
        ]
        untagged = [
            f"{method.upper()} {path}"
            for path, methods in paths.items()
            if isinstance(methods, dict)
            for method, operation in methods.items()
            if isinstance(operation, dict) and not operation.get("tags")
        ]
        destructive_without_policy = [
            f"{method.upper()} {path}"
            for path, methods in paths.items()
            if isinstance(methods, dict)
            for method, operation in methods.items()
            if method.lower() in {"delete", "patch"}
            and isinstance(operation, dict)
            and "policy" not in " ".join(str(tag).lower() for tag in operation.get("tags", []))
        ]
        health_public = "/health" in paths
        return [
            _check(
                "no_domain_route_prefixes",
                not domain_routes,
                "api",
                {"matches": domain_routes},
            ),
            _check(
                "no_raw_provider_schema_leakage",
                not any(term in serialized for term in PROVIDER_OBJECT_TERMS),
                "api",
            ),
            _check(
                "no_route_exposes_stacktrace",
                not stacktrace_routes,
                "api",
                {"matches": stacktrace_routes},
            ),
            _check(
                "routes_tagged_where_practical",
                not untagged,
                "api",
                {"matches": untagged[:25], "match_count": len(untagged)},
                severity="warning",
            ),
            _check(
                "destructive_routes_have_policy_category",
                not destructive_without_policy,
                "api",
                {"matches": destructive_without_policy},
                severity="warning",
            ),
            _check(
                "health_route_public_and_present",
                health_public,
                "api",
                severity="medium",
            ),
        ]


def _check(
    name: str,
    passed: bool,
    category: str,
    details: dict[str, Any] | None = None,
    *,
    severity: str = "high",
) -> dict[str, Any]:
    return {
        "name": name,
        "category": category,
        "status": "passed" if passed else "failed",
        "severity": severity,
        "message": f"{name} {'passed' if passed else 'failed'}.",
        "details": details or {},
    }
