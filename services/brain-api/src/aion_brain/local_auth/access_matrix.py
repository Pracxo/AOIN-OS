"""Role-aware Operator Console view filtering."""

from __future__ import annotations

from copy import deepcopy

from aion_brain.contracts.local_auth import (
    ConsoleRoleFilterRequest,
    ConsoleRoleFilterResult,
    utc_now,
)
from aion_brain.local_auth.redaction import scrub_local_auth_payload
from aion_brain.local_auth.roles import LocalRoleService
from aion_brain.telemetry.visual import build_operator_console_telemetry_event


class ConsoleRoleFilter:
    """Filter console view models by local dev role without mutation."""

    def __init__(
        self,
        *,
        role_service: LocalRoleService | None = None,
        telemetry_service: object | None = None,
    ) -> None:
        self._role_service = role_service or LocalRoleService()
        self._telemetry_service = telemetry_service

    def filter(self, request: ConsoleRoleFilterRequest) -> ConsoleRoleFilterResult:
        """Return a redacted read-only view model filtered by local roles."""
        view_model = deepcopy(request.view_model)
        safety_findings: list[dict[str, object]] = []
        filtered = scrub_local_auth_payload(view_model, findings=safety_findings)
        if not isinstance(filtered, dict):
            filtered = {}
        view = str(filtered.get("view") or "overview")
        allowed_views = self._allowed_views(request.auth_context.roles)
        removed_sections: list[str] = []
        if view not in allowed_views:
            removed_sections = [
                _section_key(section)
                for section in filtered.get("sections", [])
                if isinstance(section, dict)
            ]
            filtered["sections"] = []
            filtered["status"] = "filtered"
            filtered["summary"] = "View hidden by local role filter."
        else:
            filtered["sections"] = self._filter_sections(
                filtered.get("sections", []),
                request.auth_context.roles,
                removed_sections,
            )
        removed_actions: list[str] = []
        filtered["global_actions"] = self._filter_actions(
            filtered.get("global_actions", []),
            request.auth_context.roles,
            removed_actions,
        )
        for section in filtered.get("sections", []):
            if isinstance(section, dict):
                section["allowed_actions"] = self._filter_actions(
                    section.get("allowed_actions", []),
                    request.auth_context.roles,
                    removed_actions,
                )
        forbidden_actions = _action_keys(filtered.get("forbidden_actions", []))
        filtered["read_only"] = True
        filtered["redaction_applied"] = True
        metadata = filtered.get("metadata")
        filtered["metadata"] = {
            **(metadata if isinstance(metadata, dict) else {}),
            "local_auth_role_filter_applied": True,
            "write_actions_enabled": False,
        }
        result = ConsoleRoleFilterResult(
            status="filtered" if removed_sections or removed_actions else "unchanged",
            read_only=True,
            redaction_applied=True,
            actor_id=request.auth_context.actor_id,
            roles=request.auth_context.roles,
            filtered_view_model=filtered,
            removed_sections=removed_sections,
            removed_actions=sorted(set(removed_actions)),
            forbidden_actions=forbidden_actions,
            safety_findings=safety_findings,
            metadata={"no_write_actions_added": True},
            created_at=utc_now(),
        )
        _emit(
            self._telemetry_service,
            "local_auth_console_filtered",
            "operator_console_view",
            str(filtered.get("console_view_model_id") or "local-auth-filtered-console"),
            request.auth_context.owner_scope,
            {"status": result.status, "roles": result.roles},
        )
        return result

    def _allowed_views(self, roles: list[str]) -> set[str]:
        allowed: set[str] = set()
        for role in roles:
            read_views = self._role_service.permissions_for_roles([role]).get(
                "read_views",
                [],
            )
            if isinstance(read_views, list):
                allowed.update(view for view in read_views if isinstance(view, str))
        return allowed

    def _filter_sections(
        self,
        sections: object,
        roles: list[str],
        removed_sections: list[str],
    ) -> list[dict[str, object]]:
        if not isinstance(sections, list):
            return []
        filtered: list[dict[str, object]] = []
        for section in sections:
            if not isinstance(section, dict):
                continue
            required_roles = _required_roles(section)
            if required_roles and not set(roles).intersection(required_roles):
                removed_sections.append(_section_key(section))
                continue
            filtered.append(section)
        return filtered

    def _filter_actions(
        self,
        actions: object,
        roles: list[str],
        removed_actions: list[str],
    ) -> list[dict[str, object]]:
        if not isinstance(actions, list):
            return []
        filtered: list[dict[str, object]] = []
        for action in actions:
            if not isinstance(action, dict):
                continue
            action_key = str(action.get("action_key") or "")
            action_type = str(action.get("action_type") or "")
            allowed = False
            if action_type == "read":
                allowed = True
            elif action_type in {"dry_run", "acknowledge", "dismiss_with_reason"}:
                allowed = any(
                    self._role_service.role_allows_dry_run(role, action_key)
                    for role in roles
                )
            elif action_type == "review_record":
                allowed = any(
                    self._role_service.role_allows_review(role, action_key)
                    for role in roles
                )
            if allowed:
                safe = dict(action)
                safe["forbidden"] = False
                filtered.append(safe)
            else:
                removed_actions.append(action_key)
        return filtered


def _required_roles(section: dict[str, object]) -> set[str]:
    metadata = section.get("metadata")
    if not isinstance(metadata, dict):
        return set()
    roles = metadata.get("required_roles")
    if isinstance(roles, list):
        return {str(role) for role in roles}
    role = metadata.get("required_role")
    return {str(role)} if role else set()


def _section_key(section: dict[str, object]) -> str:
    return str(section.get("section_key") or section.get("title") or "unknown")


def _action_keys(actions: object) -> list[str]:
    if not isinstance(actions, list):
        return []
    return sorted(
        {
            str(action.get("action_key"))
            for action in actions
            if isinstance(action, dict) and action.get("action_key")
        }
    )


def _emit(
    telemetry_service: object | None,
    event_type: str,
    node_type: str,
    node_id: str,
    scope: list[str],
    payload: dict[str, object] | None = None,
) -> None:
    emit = getattr(telemetry_service, "emit", None)
    if not callable(emit):
        return
    emit(
        build_operator_console_telemetry_event(
            telemetry_id=f"telemetry-{node_id}",
            event_type=event_type,
            node_type=node_type,
            node_id=node_id,
            scope=scope,
            payload=payload,
        )
    )


__all__ = ["ConsoleRoleFilter"]
