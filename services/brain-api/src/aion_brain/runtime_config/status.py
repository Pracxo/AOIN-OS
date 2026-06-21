"""Runtime configuration status service."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from aion_brain.api_support.errors import AIONPolicyDeniedException
from aion_brain.contracts.policy import PolicyRequest
from aion_brain.contracts.runtime_config import RuntimeConfigStatus
from aion_brain.policy.base import PolicyAdapter
from aion_brain.runtime_config.profiles import _emit_runtime_config_event
from aion_brain.runtime_config.repository import RuntimeConfigRepository


class RuntimeConfigStatusService:
    """Build runtime configuration status summaries."""

    def __init__(
        self,
        repository: RuntimeConfigRepository,
        policy_adapter: PolicyAdapter,
        *,
        feature_override_service: object,
        telemetry_service: object | None = None,
        settings: object | None = None,
    ) -> None:
        self._repository = repository
        self._policy_adapter = policy_adapter
        self._feature_override_service = feature_override_service
        self._telemetry_service = telemetry_service
        self._settings = settings

    def status(self, scope: list[str]) -> RuntimeConfigStatus:
        """Return effective runtime configuration status without secrets."""
        self._authorize("runtime_config.status.read", scope)
        active_profile = self._repository.active_profile()
        feature_overrides = self._repository.list_overrides(status="active")
        effective_flags = self._effective_flags(scope)
        latest_validation = self._repository.latest_validation_run()
        latest_snapshot = self._repository.latest_snapshot()
        status = RuntimeConfigStatus(
            active_profile=active_profile,
            feature_overrides=feature_overrides,
            effective_feature_flags=effective_flags,
            safe_defaults_ok=(
                latest_validation is None or latest_validation.status in {"passed", "warning"}
            ),
            validation_status=latest_validation.status if latest_validation else "warning",
            latest_snapshot_id=latest_snapshot.config_snapshot_id if latest_snapshot else None,
            generated_at=datetime.now(UTC),
        )
        _emit_runtime_config_event(
            self._telemetry_service,
            event_type="runtime_config_status_read",
            node_type="config",
            node_id="runtime-config-status",
            scope=scope,
            intensity=0.4,
        )
        return status

    def _effective_flags(self, scope: list[str]) -> dict[str, bool]:
        effective_flags = getattr(self._feature_override_service, "effective_flags", None)
        if callable(effective_flags):
            try:
                flags = dict(effective_flags(scope))
            except Exception:
                flags = {}
        else:
            flags = {}
        settings = getattr(self._repository, "_settings", None)
        settings = settings or getattr(self, "_settings", None)
        if settings is not None:
            flags.update(_contract_registry_flags(settings))
            flags.update(_extension_flags(settings))
        return flags

    def _authorize(self, action_type: str, scope: list[str]) -> None:
        decision = self._policy_adapter.authorize(
            PolicyRequest(
                request_id=f"{action_type}-{uuid4().hex}",
                trace_id=None,
                actor_id=None,
                workspace_id=None,
                action_type=action_type,
                resource_type="runtime_config_status",
                resource_id=None,
                risk_level="low",
                approval_present=True,
                requested_permissions=[action_type],
                security_scope=scope,
                context={},
            )
        )
        if not decision.allow:
            raise AIONPolicyDeniedException(decision.reason)


def _contract_registry_flags(settings: object) -> dict[str, bool]:
    return {
        "contract_registry.enabled": bool(getattr(settings, "contract_registry_enabled", True)),
        "contract_registry.snapshot_enabled": bool(
            getattr(settings, "contract_snapshot_enabled", True)
        ),
        "contract_registry.compatibility_scan_enabled": bool(
            getattr(settings, "compatibility_scan_enabled", True)
        ),
        "contract_registry.interface_inventory_enabled": bool(
            getattr(settings, "interface_inventory_enabled", True)
        ),
        "contract_registry.auto_snapshot_enabled": bool(
            getattr(settings, "contract_registry_auto_snapshot_enabled", False)
        ),
        "contract_registry.breaking_changes_fail_freeze": bool(
            getattr(settings, "compatibility_breaking_changes_fail_freeze", True)
        ),
    }


def _extension_flags(settings: object) -> dict[str, bool]:
    return {
        "extensions.enabled": bool(getattr(settings, "extensions_enabled", True)),
        "extension_registry.enabled": bool(
            getattr(settings, "extension_registry_enabled", True)
        ),
        "extension_manifest_validation.enabled": bool(
            getattr(settings, "extension_manifest_validation_enabled", True)
        ),
        "extension_compatibility_gate.enabled": bool(
            getattr(settings, "extension_compatibility_gate_enabled", True)
        ),
        "extension_install_plans.enabled": bool(
            getattr(settings, "extension_install_plans_enabled", True)
        ),
        "extension_code_loading.enabled": bool(
            getattr(settings, "extension_code_loading_enabled", False)
        ),
        "extension_activation.enabled": bool(
            getattr(settings, "extension_activation_enabled", False)
        ),
        "extension_external_sources.enabled": bool(
            getattr(settings, "extension_external_sources_enabled", False)
        ),
    }
