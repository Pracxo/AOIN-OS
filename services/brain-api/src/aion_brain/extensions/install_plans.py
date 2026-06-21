"""Future extension install plan service."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, cast
from uuid import uuid4

from aion_brain.api_support.errors import AIONNotFoundException
from aion_brain.contracts.extensions import ExtensionInstallPlan, ExtensionPackage
from aion_brain.extensions.policy import authorize_extension_action
from aion_brain.extensions.repository import ExtensionRegistryRepository
from aion_brain.extensions.telemetry import emit_extension_telemetry


class InstallPlanService:
    """Create non-executable future install plans."""

    def __init__(
        self,
        repository: ExtensionRegistryRepository,
        policy_adapter: object,
        *,
        telemetry_service: object | None = None,
        settings: object | None = None,
    ) -> None:
        self._repository = repository
        self._policy_adapter = policy_adapter
        self._telemetry_service = telemetry_service
        self._settings = settings

    def create_plan(
        self,
        package: ExtensionPackage,
        *,
        scope: list[str] | None = None,
        created_by: str | None = None,
    ) -> ExtensionInstallPlan:
        """Create a metadata-only plan that cannot execute in v0.1."""

        owner_scope = scope or package.owner_scope
        authorize_extension_action(
            self._policy_adapter,
            "extension.install_plan.create",
            owner_scope,
            actor_id=created_by or package.actor_id,
            workspace_id=package.workspace_id,
            trace_id=package.trace_id,
            resource_type="extension_install_plan",
            resource_id=package.extension_package_id,
            risk_level="medium",
        )
        blockers = _install_blockers(package, self._settings)
        warnings = _install_warnings(package)
        plan = ExtensionInstallPlan(
            install_plan_id=f"extension-install-plan-{uuid4().hex}",
            extension_package_id=package.extension_package_id,
            trace_id=package.trace_id,
            status=cast(Any, "blocked" if blockers else "planned"),
            plan_type="future_install",
            owner_scope=owner_scope,
            steps=[
                {
                    "step": "validate_manifest",
                    "status": "metadata_only",
                    "executable": False,
                },
                {
                    "step": "check_compatibility",
                    "status": "metadata_only",
                    "executable": False,
                },
                {
                    "step": "operator_review",
                    "status": "required",
                    "executable": False,
                },
                {
                    "step": "future_install_reserved",
                    "status": "not_implemented",
                    "executable": False,
                },
            ],
            required_approvals=["operator.review"],
            required_settings=[
                "extensions.enabled",
                "extension_registry.enabled",
                "extension_code_loading.enabled:false",
                "extension_activation.enabled:false",
            ],
            required_policy_actions=list(package.declared_policy_actions),
            required_contracts=[
                str(item.get("contract_key") or item.get("key"))
                for item in package.declared_contracts
                if item.get("contract_key") or item.get("key")
            ],
            required_sandbox_profiles=_sandbox_profiles(package),
            blocked=bool(blockers),
            blockers=blockers,
            warnings=warnings,
            executable=False,
            execution_allowed=False,
            metadata={
                "v0_1_metadata_only": True,
                "activation_allowed": False,
                "code_loading_allowed": False,
            },
            created_by=created_by or package.created_by,
            created_at=datetime.now(UTC),
        )
        saved = self._repository.save_install_plan(plan)
        self._repository.save_package(
            package.model_copy(
                update={
                    "install_plan_id": saved.install_plan_id,
                    "updated_at": datetime.now(UTC),
                }
            )
        )
        emit_extension_telemetry(
            self._telemetry_service,
            event_type="extension_install_plan_created",
            node_type="extension_install_plan",
            node_id=saved.install_plan_id,
            scope=saved.owner_scope,
            intensity=0.5,
            payload={"blocked": saved.blocked, "extension_package_id": saved.extension_package_id},
        )
        return saved

    def get_plan(self, install_plan_id: str, scope: list[str]) -> ExtensionInstallPlan | None:
        authorize_extension_action(
            self._policy_adapter,
            "extension.install_plan.read",
            scope,
            resource_type="extension_install_plan",
            resource_id=install_plan_id,
            risk_level="low",
        )
        return self._repository.get_install_plan(install_plan_id)

    def require_plan(self, install_plan_id: str, scope: list[str]) -> ExtensionInstallPlan:
        plan = self.get_plan(install_plan_id, scope)
        if plan is None:
            raise AIONNotFoundException("extension_install_plan_not_found")
        return plan

    def list_plans(
        self,
        scope: list[str],
        *,
        status: str | None = None,
        extension_package_id: str | None = None,
        limit: int = 100,
    ) -> list[ExtensionInstallPlan]:
        authorize_extension_action(
            self._policy_adapter,
            "extension.install_plan.read",
            scope,
            resource_type="extension_install_plan",
            risk_level="low",
        )
        return self._repository.list_install_plans(
            status=status,
            extension_package_id=extension_package_id,
            limit=limit,
        )


def _install_blockers(package: ExtensionPackage, settings: object | None) -> list[dict[str, Any]]:
    blockers = [
        {
            "code": "install_not_implemented",
            "severity": "high",
            "message": "Extension installation is reserved for a later AION task.",
        }
    ]
    if bool(getattr(settings, "extension_code_loading_enabled", False)):
        blockers.append(
            {
                "code": "code_loading_enabled",
                "severity": "critical",
                "message": "Extension code loading must remain disabled in v0.1.",
            }
        )
    if bool(getattr(settings, "extension_activation_enabled", False)):
        blockers.append(
            {
                "code": "activation_enabled",
                "severity": "critical",
                "message": "Extension activation must remain disabled in v0.1.",
            }
        )
    if package.compatibility_status in {"failed", "blocked"}:
        blockers.append(
            {
                "code": "compatibility_not_passed",
                "severity": "high",
                "message": "Compatibility status must pass before future installation.",
            }
        )
    return blockers


def _install_warnings(package: ExtensionPackage) -> list[dict[str, Any]]:
    warnings: list[dict[str, Any]] = []
    if package.review_status != "approved":
        warnings.append(
            {
                "code": "review_required",
                "severity": "medium",
                "message": "Operator review is required before future installation.",
            }
        )
    return warnings


def _sandbox_profiles(package: ExtensionPackage) -> list[str]:
    requirements = package.manifest.sandbox_requirements
    profile = requirements.get("profile") or requirements.get("sandbox_profile")
    return [str(profile)] if profile else []


__all__ = ["InstallPlanService"]
