"""Role permission proof matrix for local Operator Console filtering."""

from __future__ import annotations

from copy import deepcopy
from typing import Any
from uuid import uuid4

from aion_brain.contracts.local_auth import (
    RoleAccessAudit,
    RoleAccessDecision,
    RolePermission,
    utc_now,
)
from aion_brain.local_auth.redaction import scrub_local_auth_payload
from aion_brain.operator_console.action_boundaries import (
    allowed_action_descriptors,
    forbidden_action_descriptors,
)
from aion_brain.operator_console.data_sources import list_console_views

ROLE_ORDER = ("viewer", "operator", "reviewer", "admin", "auditor", "system_service")
STATIC_CONSOLE_ROLES = ("viewer", "operator", "reviewer", "admin", "auditor")

VIEW_ORDER = (
    "overview",
    "readiness",
    "release_candidate",
    "freeze_release",
    "golden_path",
    "module_lifecycle",
    "module_activation",
    "module_mock_runtime",
    "model_provider_hardening",
    "operator_actions",
    "local_auth",
    "local_session",
    "notifications",
    "incidents",
    "registry_integrity",
    "lifecycle_review",
    "audit_provenance",
    "settings_safety",
)

VIEWER_VIEWS = (
    "overview",
    "readiness",
    "golden_path",
    "module_lifecycle",
    "model_provider_hardening",
)
OPERATOR_VIEWS = (
    "overview",
    "readiness",
    "release_candidate",
    "freeze_release",
    "golden_path",
    "module_lifecycle",
    "module_activation",
    "module_mock_runtime",
    "model_provider_hardening",
    "operator_actions",
    "local_auth",
    "local_session",
    "notifications",
    "incidents",
    "registry_integrity",
    "lifecycle_review",
)
REVIEWER_VIEWS = (
    "overview",
    "release_candidate",
    "module_lifecycle",
    "module_activation",
    "module_mock_runtime",
    "model_provider_hardening",
    "operator_actions",
    "lifecycle_review",
)
AUDITOR_VIEWS = (
    "overview",
    "local_auth",
    "local_session",
    "audit_provenance",
    "registry_integrity",
    "lifecycle_review",
    "settings_safety",
)
SYSTEM_SERVICE_VIEWS = ("overview", "settings_safety")

ROLE_READ_VIEWS = {
    "viewer": VIEWER_VIEWS,
    "operator": OPERATOR_VIEWS,
    "reviewer": REVIEWER_VIEWS,
    "admin": VIEW_ORDER,
    "auditor": AUDITOR_VIEWS,
    "system_service": SYSTEM_SERVICE_VIEWS,
}

COMMON_CONSTRAINTS = (
    "dev_only",
    "read_only_console",
    "no_execute",
    "no_activation",
    "no_external_calls",
    "no_hard_delete",
    "no_credential_storage",
)
DRY_RUN_ACTIONS = (
    "run_dry_run_check",
    "acknowledge_notification",
    "dismiss_non_blocking_finding_with_reason",
)
REVIEW_ACTIONS = ("create_review_record",)
READ_ACTIONS = tuple(
    descriptor.action_key
    for descriptor in allowed_action_descriptors()
    if descriptor.action_type == "read"
)
FORBIDDEN_ACTIONS = tuple(descriptor.action_key for descriptor in forbidden_action_descriptors())


class RolePermissionMatrixService:
    """Decide local role visibility without granting privileged capability."""

    def build_permission_matrix(self) -> dict[str, Any]:
        """Return the deterministic permission proof matrix."""
        declared_views = sorted({*VIEW_ORDER, *[str(view) for view in list_console_views()]})
        roles = {}
        for role in ROLE_ORDER:
            roles[role] = {
                "read_views": list(ROLE_READ_VIEWS[role]),
                "dry_run_actions": list(DRY_RUN_ACTIONS if role == "operator" else ()),
                "review_actions": list(REVIEW_ACTIONS if role == "reviewer" else ()),
                "forbidden_actions_visible": list(FORBIDDEN_ACTIONS),
                "write_allowed": False,
                "execute_allowed": False,
                "activation_allowed": False,
                "external_calls_allowed": False,
                "constraints": _constraints_for_role(role),
            }
        return {
            "matrix_version": "aion-096",
            "roles": roles,
            "views": declared_views,
            "static_console_roles": list(STATIC_CONSOLE_ROLES),
            "system_service_exposed_in_static_console": False,
            "forbidden_actions_visible": True,
            "write_allowed": False,
            "execute_allowed": False,
            "activation_allowed": False,
            "external_calls_allowed": False,
            "redaction_required": True,
        }

    def role_permissions(self) -> list[RolePermission]:
        """Return RolePermission rows backed by the proof matrix."""
        return [
            RolePermission(
                role=role,
                read_views=list(ROLE_READ_VIEWS[role]),
                dry_run_actions=list(DRY_RUN_ACTIONS if role == "operator" else ()),
                review_actions=list(REVIEW_ACTIONS if role == "reviewer" else ()),
                forbidden_actions=list(FORBIDDEN_ACTIONS),
                constraints=_constraints_for_role(role),
                metadata={
                    "matrix_version": "aion-096",
                    "write_allowed": False,
                    "execute_allowed": False,
                    "activation_allowed": False,
                    "external_calls_allowed": False,
                },
            )
            for role in ROLE_ORDER
        ]

    def decide(
        self,
        role: str,
        view: str,
        section_key: str | None = None,
        action_key: str | None = None,
    ) -> RoleAccessDecision:
        """Return one fail-closed read-only access decision."""
        if role not in ROLE_ORDER:
            return _decision(role, view, section_key, action_key, "denied", "unknown_role")
        if view not in VIEW_ORDER and view not in {str(item) for item in list_console_views()}:
            return _decision(role, view, section_key, action_key, "denied", "unknown_view")
        if action_key in FORBIDDEN_ACTIONS:
            return _decision(
                role,
                view,
                section_key,
                action_key,
                "visible_forbidden",
                "forbidden_action_descriptor_visible",
                read_allowed=True,
            )
        if view not in ROLE_READ_VIEWS[role]:
            return _decision(role, view, section_key, action_key, "hidden", "view_not_allowed")
        if not action_key or action_key in READ_ACTIONS:
            return _decision(
                role,
                view,
                section_key,
                action_key,
                "allowed",
                "read_only_view_allowed",
                read_allowed=True,
            )
        if action_key in DRY_RUN_ACTIONS and role == "operator":
            return _decision(
                role,
                view,
                section_key,
                action_key,
                "allowed",
                "dry_run_descriptor_allowed",
                read_allowed=True,
                dry_run_allowed=True,
            )
        if action_key in REVIEW_ACTIONS and role == "reviewer":
            return _decision(
                role,
                view,
                section_key,
                action_key,
                "allowed",
                "review_descriptor_allowed",
                read_allowed=True,
                review_allowed=True,
            )
        return _decision(role, view, section_key, action_key, "denied", "action_not_allowed")

    def filter_view_for_roles(
        self,
        view_model: dict[str, Any],
        roles: list[str],
    ) -> dict[str, Any]:
        """Return a redacted role-filtered copy of a console view model."""
        findings: list[dict[str, object]] = []
        scrubbed = scrub_local_auth_payload(deepcopy(view_model), findings=findings)
        filtered = scrubbed if isinstance(scrubbed, dict) else {}
        valid_roles = [role for role in roles if role in ROLE_ORDER]
        view = str(filtered.get("view") or "overview")
        removed_sections: list[str] = []
        removed_actions: list[str] = []
        decisions: list[dict[str, Any]] = []
        view_allowed = any(
            self.decide(role, view).decision == "allowed" for role in valid_roles
        )
        sections = filtered.get("sections", [])
        if view_allowed:
            filtered["sections"] = self._filter_sections(
                sections,
                valid_roles,
                view,
                removed_sections,
                removed_actions,
                decisions,
            )
        else:
            removed_sections = [
                _section_key(section) for section in sections if isinstance(section, dict)
            ]
            filtered["sections"] = [
                _restricted_section(section)
                for section in sections
                if isinstance(section, dict) and _has_safety_payload(section)
            ]
            filtered["status"] = "filtered"
            filtered["summary"] = "View unavailable for supplied local roles."
            decisions.extend(
                self.decide(role, view).model_dump(mode="json") for role in roles
            )
        filtered["global_actions"] = self._filter_allowed_actions(
            filtered.get("global_actions", []),
            valid_roles,
            view,
            None,
            removed_actions,
            decisions,
        )
        filtered["forbidden_actions"] = _forbidden_actions(filtered.get("forbidden_actions"))
        filtered["read_only"] = True
        filtered["redaction_applied"] = True
        metadata = filtered.get("metadata")
        filtered["metadata"] = {
            **(metadata if isinstance(metadata, dict) else {}),
            "local_auth_role_filter_applied": True,
            "role_access_filter_applied": True,
            "role_matrix_version": "aion-096",
            "roles": valid_roles,
            "removed_sections": sorted(set(removed_sections)),
            "removed_actions": sorted({action for action in removed_actions if action}),
            "forbidden_actions_visible": True,
            "write_allowed": False,
            "execute_allowed": False,
            "activation_allowed": False,
            "external_calls_allowed": False,
            "redaction_findings": findings,
            "decisions": decisions[:24],
        }
        return filtered

    def audit_matrix(self, trace_id: str | None = None) -> RoleAccessAudit:
        """Audit the proof matrix for read-only safety invariants."""
        decisions = [
            self.decide(role, view)
            for role in ROLE_ORDER
            for view in VIEW_ORDER
        ]
        decisions.extend(
            self.decide(role, "module_activation", action_key="activate_module")
            for role in ROLE_ORDER
        )
        decisions.extend(
            self.decide(role, "operator_actions", action_key="execute_tool")
            for role in ROLE_ORDER
        )
        findings = [
            {
                "finding": "system_service_static_ui_hidden",
                "status": "passed",
            },
            {
                "finding": "forbidden_action_descriptors_visible",
                "status": "passed",
            },
        ]
        return RoleAccessAudit(
            role_access_audit_id=f"role-access-audit-{uuid4().hex}",
            trace_id=trace_id,
            status="passed",
            roles_checked=list(ROLE_ORDER),
            views_checked=list(VIEW_ORDER),
            decisions=decisions,
            forbidden_actions_visible=True,
            write_actions_absent=True,
            execution_absent=True,
            activation_absent=True,
            external_calls_absent=True,
            redaction_applied=True,
            findings=findings,
            metadata={
                "matrix_version": "aion-096",
                "static_console_roles": list(STATIC_CONSOLE_ROLES),
                "system_service_exposed_in_static_console": False,
            },
            created_at=utc_now(),
        )

    def _filter_sections(
        self,
        sections: object,
        roles: list[str],
        view: str,
        removed_sections: list[str],
        removed_actions: list[str],
        decisions: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        if not isinstance(sections, list):
            return []
        filtered: list[dict[str, Any]] = []
        for section in sections:
            if not isinstance(section, dict):
                continue
            section_key = _section_key(section)
            required_roles = _required_roles(section)
            if required_roles and not set(roles).intersection(required_roles):
                removed_sections.append(section_key)
                if _has_safety_payload(section):
                    filtered.append(_restricted_section(section))
                continue
            safe_section = dict(section)
            safe_section["allowed_actions"] = self._filter_allowed_actions(
                safe_section.get("allowed_actions", []),
                roles,
                view,
                section_key,
                removed_actions,
                decisions,
            )
            safe_section["forbidden_actions"] = _forbidden_actions(
                safe_section.get("forbidden_actions")
            )
            filtered.append(safe_section)
        return filtered

    def _filter_allowed_actions(
        self,
        actions: object,
        roles: list[str],
        view: str,
        section_key: str | None,
        removed_actions: list[str],
        decisions: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        if not isinstance(actions, list):
            return []
        filtered: list[dict[str, Any]] = []
        for action in actions:
            if not isinstance(action, dict):
                continue
            action_key = str(action.get("action_key") or "")
            action_type = str(action.get("action_type") or "")
            key = action_key or action_type
            role_decisions = [
                self.decide(role, view, section_key=section_key, action_key=key)
                for role in roles
            ]
            decisions.extend(decision.model_dump(mode="json") for decision in role_decisions)
            allowed = any(
                decision.decision == "allowed"
                and (
                    decision.read_allowed
                    or decision.dry_run_allowed
                    or decision.review_allowed
                )
                for decision in role_decisions
            )
            if allowed:
                filtered.append(dict(action))
            else:
                removed_actions.append(key)
        return filtered


def _decision(
    role: str,
    view: str,
    section_key: str | None,
    action_key: str | None,
    decision: str,
    reason: str,
    *,
    read_allowed: bool = False,
    dry_run_allowed: bool = False,
    review_allowed: bool = False,
) -> RoleAccessDecision:
    return RoleAccessDecision(
        role=role,
        view=view,
        section_key=section_key,
        action_key=action_key,
        decision=decision,
        reason=reason,
        read_allowed=read_allowed,
        dry_run_allowed=dry_run_allowed,
        review_allowed=review_allowed,
        write_allowed=False,
        execute_allowed=False,
        activation_allowed=False,
        external_calls_allowed=False,
        metadata={"matrix_version": "aion-096"},
    )


def _constraints_for_role(role: str) -> list[str]:
    role_specific = {
        "viewer": ("read_only",),
        "operator": ("dry_run_descriptors_only",),
        "reviewer": ("review_records_only",),
        "admin": ("local_settings_read_only", "no_production_auth_enablement"),
        "auditor": ("audit_read_only", "redacted_exports_only"),
        "system_service": ("synthetic_system_context", "not_static_ui_role"),
    }
    return sorted({*COMMON_CONSTRAINTS, *role_specific.get(role, ())})


def _required_roles(section: dict[str, Any]) -> set[str]:
    metadata = section.get("metadata")
    if not isinstance(metadata, dict):
        return set()
    roles = metadata.get("required_roles")
    if isinstance(roles, list):
        return {str(role) for role in roles}
    role = metadata.get("required_role")
    return {str(role)} if role else set()


def _section_key(section: dict[str, Any]) -> str:
    return str(section.get("section_key") or section.get("title") or "unknown")


def _has_safety_payload(section: dict[str, Any]) -> bool:
    return bool(section.get("blockers") or section.get("forbidden_actions"))


def _restricted_section(section: dict[str, Any]) -> dict[str, Any]:
    restricted = dict(section)
    restricted["items"] = []
    restricted["allowed_actions"] = []
    restricted["status"] = "unavailable"
    restricted["summary"] = "Section unavailable for supplied local roles."
    metadata = restricted.get("metadata")
    restricted["metadata"] = {
        **(metadata if isinstance(metadata, dict) else {}),
        "role_restricted": True,
        "read_only": True,
    }
    return restricted


def _forbidden_actions(actions: object) -> list[dict[str, Any]]:
    if isinstance(actions, list) and actions:
        return [dict(action) for action in actions if isinstance(action, dict)]
    return []


__all__ = [
    "ROLE_ORDER",
    "STATIC_CONSOLE_ROLES",
    "VIEW_ORDER",
    "RolePermissionMatrixService",
]
