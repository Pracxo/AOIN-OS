"""Extension registry query service."""

from __future__ import annotations

from aion_brain.contracts.extensions import ExtensionQuery, ExtensionQueryResult
from aion_brain.extensions.policy import authorize_extension_action
from aion_brain.extensions.repository import ExtensionRegistryRepository


class ExtensionQueryService:
    """Query extension registry records through AION-owned contracts."""

    def __init__(self, repository: ExtensionRegistryRepository, policy_adapter: object) -> None:
        self._repository = repository
        self._policy_adapter = policy_adapter

    def query(self, request: ExtensionQuery) -> ExtensionQueryResult:
        authorize_extension_action(
            self._policy_adapter,
            "extension.query",
            request.scope,
            resource_type="extension_registry",
            risk_level="low",
            context=request.model_dump(mode="json"),
        )
        packages = self._repository.list_packages(
            status=request.status,
            package_type=request.package_type,
            compatibility_status=request.compatibility_status,
            review_status=request.review_status,
            include_deleted=request.include_deleted,
            limit=request.limit,
        )
        if request.query:
            query = request.query.lower()
            packages = [
                package
                for package in packages
                if query in package.extension_key.lower()
                or query in package.name.lower()
                or query in package.description.lower()
            ]
        return ExtensionQueryResult(
            packages=packages,
            compatibility_runs=self._repository.list_compatibility_runs(limit=request.limit),
            reviews=self._repository.list_reviews(limit=request.limit),
            install_plans=self._repository.list_install_plans(limit=request.limit),
            total_count=len(packages),
            constraints=[
                "metadata_only",
                "no_extension_code_loading",
                "no_extension_activation",
            ],
            metadata={"source_mutated": False},
        )


__all__ = ["ExtensionQueryService"]
