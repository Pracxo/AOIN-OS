"""Policy-gated semantic memory service."""

from datetime import UTC, datetime

from aion_brain.audit.repository import AuditRepository
from aion_brain.contracts.memory import (
    MemoryRecord,
    SemanticAdapterStatus,
    SemanticIndexResponse,
    SemanticMemoryQuery,
    SemanticMemoryResult,
    TurboVecIndexStatus,
    TurboVecRebuildRequest,
    TurboVecRebuildResponse,
)
from aion_brain.contracts.policy import PolicyDecision, PolicyRequest
from aion_brain.contracts.telemetry import VisualTelemetryEvent
from aion_brain.memory.base import SemanticMemoryAdapter
from aion_brain.policy.base import PolicyAdapter


class SemanticMemoryPolicyDenied(Exception):
    """Raised when policy denies semantic memory work."""

    def __init__(self, decision: PolicyDecision) -> None:
        super().__init__(decision.reason)
        self.decision = decision


class SemanticMemoryUnavailable(Exception):
    """Raised when the selected semantic adapter is unavailable."""

    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


class SemanticMemoryService:
    """Policy-gated semantic memory boundary."""

    def __init__(
        self,
        *,
        adapter: SemanticMemoryAdapter,
        policy_adapter: PolicyAdapter,
        telemetry_repository: AuditRepository | None = None,
        configured_adapter: str | None = None,
        fallback_reason: str | None = None,
        turbovec_adapter: SemanticMemoryAdapter | None = None,
        degraded_mode_service: object | None = None,
    ) -> None:
        self._adapter = adapter
        self._policy_adapter = policy_adapter
        self._telemetry_repository = telemetry_repository
        self._configured_adapter: str = configured_adapter or str(
            getattr(adapter, "adapter_name", "unknown")
        )
        self._fallback_reason = fallback_reason
        self._turbovec_adapter = turbovec_adapter
        self._degraded_mode_service = degraded_mode_service

    def set_degraded_mode_service(self, degraded_mode_service: object | None) -> None:
        """Attach degraded mode service after kernel assembly."""
        self._degraded_mode_service = degraded_mode_service

    def remember(self, record: MemoryRecord) -> str:
        """Index a memory record after policy authorization."""
        self._ensure_allowed(
            action_type="memory.write",
            resource_id=record.memory_id,
            risk_level=_risk_from_sensitivity(record.sensitivity),
            scope=record.owner_scope,
            context={"operation": "semantic_index"},
        )
        return self._adapter.remember(record)

    def retrieve(self, query: SemanticMemoryQuery) -> list[SemanticMemoryResult]:
        """Retrieve semantic memories after policy authorization."""
        self._ensure_allowed(
            action_type="memory.retrieve",
            resource_id=None,
            risk_level="low",
            scope=query.scope,
            context={"operation": "semantic_retrieve", "memory_types": query.memory_types},
        )
        try:
            results = self._adapter.retrieve(query)
        except RuntimeError as exc:
            self._enter_degraded("semantic_memory", str(exc), query.scope)
            raise SemanticMemoryUnavailable(str(exc)) from exc
        self._emit_retrieval_telemetry(results)
        if self._fallback_reason:
            results = [
                result.model_copy(
                    update={
                        "metadata": {
                            **result.metadata,
                            "adapter_fallback": True,
                            "fallback_reason": self._fallback_reason,
                        }
                    }
                )
                for result in results
            ]
        return results

    def reindex(self, memory_id: str, scope: list[str]) -> SemanticIndexResponse:
        """Reindex one memory after policy authorization."""
        self._ensure_allowed(
            action_type="memory.write",
            resource_id=memory_id,
            risk_level="low",
            scope=scope,
            context={"operation": "semantic_reindex"},
        )
        try:
            return self._adapter.reindex(memory_id)
        except RuntimeError as exc:
            self._enter_degraded("semantic_memory", str(exc), scope)
            raise SemanticMemoryUnavailable(str(exc)) from exc

    def forget(self, memory_id: str, scope: list[str]) -> bool:
        """Forget semantic vectors after policy authorization."""
        self._ensure_allowed(
            action_type="memory.write",
            resource_id=memory_id,
            risk_level="low",
            scope=scope,
            context={"operation": "semantic_forget"},
        )
        return self._adapter.forget(memory_id)

    def adapter_statuses(self, scope: list[str]) -> list[SemanticAdapterStatus]:
        """Return public semantic adapter status summaries."""
        self._ensure_allowed(
            action_type="memory.retrieve",
            resource_id=None,
            risk_level="low",
            scope=scope,
            context={"operation": "semantic_adapter_status"},
        )
        active_name = _normalized_adapter_name(self._adapter.adapter_name)
        default_name = _normalized_adapter_name(self._configured_adapter)
        turbovec_status = self.turbovec_status("default", scope, authorize=False)
        return [
            SemanticAdapterStatus(
                adapter_name="in_memory",
                active=active_name in {"in_memory", "in-memory"},
                available=True,
                default=default_name in {"in_memory", "in-memory"},
                reason=None,
                metadata={},
            ),
            SemanticAdapterStatus(
                adapter_name="pgvector",
                active=active_name == "pgvector",
                available=True,
                default=default_name == "pgvector",
                reason=self._fallback_reason if active_name == "pgvector" else None,
                metadata={
                    "adapter_fallback": bool(self._fallback_reason)
                    if active_name == "pgvector"
                    else False
                },
            ),
            SemanticAdapterStatus(
                adapter_name="turbovec",
                active=active_name == "turbovec",
                available=turbovec_status.available,
                default=default_name == "turbovec",
                reason=turbovec_status.reason,
                metadata={
                    "status": turbovec_status.status,
                    "index_name": turbovec_status.index_name,
                    "entry_count": turbovec_status.entry_count,
                },
            ),
        ]

    def turbovec_status(
        self,
        index_name: str = "default",
        scope: list[str] | None = None,
        *,
        authorize: bool = True,
    ) -> TurboVecIndexStatus:
        """Return TurboVec status without exposing vendor objects."""
        if authorize:
            self._ensure_allowed(
                action_type="memory.retrieve",
                resource_id=None,
                risk_level="low",
                scope=scope or ["workspace:main"],
                context={"operation": "turbovec_status", "index_name": index_name},
            )
        adapter = self._turbovec_adapter or self._adapter
        status = adapter.status(index_name)
        if status is None:
            now = datetime.now(UTC)
            return TurboVecIndexStatus(
                index_id=f"turbovec-{index_name}",
                index_name=index_name,
                adapter_name="turbovec",
                dimensions=1,
                bit_width=4,
                index_path="unavailable",
                status="unavailable",
                entry_count=0,
                available=False,
                reason="turbovec_not_configured",
                metadata={},
                created_at=now,
                updated_at=now,
                rebuilt_at=None,
            )
        return status

    def _enter_degraded(self, component: str, reason: str, scope: list[str]) -> None:
        enter = getattr(self._degraded_mode_service, "enter", None)
        if not callable(enter):
            return
        try:
            enter(
                component=component,
                severity="medium",
                reason=reason,
                dependencies=[self._configured_adapter],
                fallbacks_active=["local_baseline"] if self._fallback_reason else [],
                constraints=["semantic_recall_degraded"],
                trace_id=scope[0] if scope else None,
            )
        except Exception:
            return

    def rebuild_turbovec(self, request: TurboVecRebuildRequest) -> TurboVecRebuildResponse:
        """Policy-gate and rebuild the TurboVec index."""
        self._ensure_allowed(
            action_type="memory.write",
            resource_id=request.index_name,
            risk_level="medium" if request.limit > 100000 else "low",
            scope=request.scope,
            context={
                "operation": "turbovec_rebuild",
                "limit": request.limit,
                "approval_required": request.limit > 100000,
            },
        )
        adapter = self._turbovec_adapter or self._adapter
        try:
            return adapter.rebuild(request)
        except RuntimeError as exc:
            raise SemanticMemoryUnavailable(str(exc)) from exc

    def reindex_turbovec(
        self,
        memory_id: str,
        *,
        index_name: str,
        force: bool,
        scope: list[str],
    ) -> SemanticIndexResponse:
        """Policy-gate and reindex one memory through TurboVec."""
        self._ensure_allowed(
            action_type="memory.write",
            resource_id=memory_id,
            risk_level="low",
            scope=scope,
            context={
                "operation": "turbovec_reindex",
                "index_name": index_name,
                "force": force,
            },
        )
        adapter = self._turbovec_adapter or self._adapter
        try:
            return adapter.reindex(memory_id)
        except RuntimeError as exc:
            raise SemanticMemoryUnavailable(str(exc)) from exc

    @property
    def active_adapter_name(self) -> str:
        """Return the selected semantic adapter name."""
        return self._adapter.adapter_name

    @property
    def fallback_reason(self) -> str | None:
        """Return the selected semantic adapter fallback reason."""
        return self._fallback_reason

    def _ensure_allowed(
        self,
        *,
        action_type: str,
        resource_id: str | None,
        risk_level: str,
        scope: list[str],
        context: dict[str, object],
    ) -> None:
        decision = self._policy_adapter.authorize(
            PolicyRequest(
                request_id=f"{action_type}-{resource_id or 'semantic'}",
                trace_id=None,
                actor_id=None,
                workspace_id=None,
                action_type=action_type,
                resource_type="memory",
                resource_id=resource_id,
                risk_level=risk_level,
                approval_present=False,
                requested_permissions=[],
                security_scope=scope,
                context=context,
            )
        )
        if not decision.allow:
            raise SemanticMemoryPolicyDenied(decision)

    def _emit_retrieval_telemetry(self, results: list[SemanticMemoryResult]) -> None:
        if self._telemetry_repository is None or not results:
            return
        trace_id = f"semantic-retrieve-{datetime.now(UTC).timestamp()}"
        events = [
            VisualTelemetryEvent(
                telemetry_id=f"telemetry-{trace_id}-{result.memory.memory_id}",
                trace_id=trace_id,
                event_type="memory_node_activated",
                node_type="memory",
                node_id=result.memory.memory_id,
                edge_from=None,
                edge_to=None,
                intensity=result.score,
                payload={
                    "adapter_name": result.adapter_name,
                    "retrieval_source": result.retrieval_source,
                },
                created_at=datetime.now(UTC),
            )
            for result in results
        ]
        try:
            self._telemetry_repository.save_visual_telemetry(trace_id, events)
        except Exception:
            return


def _risk_from_sensitivity(sensitivity: str) -> str:
    normalized = sensitivity.lower()
    if normalized in {"high", "critical"}:
        return "high"
    if normalized == "medium":
        return "medium"
    return "low"


def _normalized_adapter_name(value: str) -> str:
    return value.replace("-", "_")
