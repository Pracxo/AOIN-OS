"""Lifecycle evaluation orchestration."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, cast
from uuid import uuid4

from aion_brain.audit_integrity.ledger import record_audit_event
from aion_brain.contracts.incidents import IncidentSignalCreateRequest
from aion_brain.contracts.lifecycle import (
    ArchiveCandidate,
    LifecycleEvaluationRequest,
    LifecycleEvaluationRun,
    LifecycleReviewRecord,
    LifecycleRunStatus,
    PurgePreview,
    RedactionCandidate,
)
from aion_brain.contracts.notifications import NotificationPublishRequest
from aion_brain.contracts.resource_registry import ResourceDescriptor, ResourceRegistryQuery
from aion_brain.contracts.retention import (
    LifecyclePolicy,
    LifecyclePolicyCreateRequest,
    RetentionClassification,
)
from aion_brain.contracts.root_cause import IncidentSeverity
from aion_brain.contracts.scopes import ActorContext
from aion_brain.dialogue._shared import authorize, emit_telemetry
from aion_brain.lifecycle.policies import default_lifecycle_policy_requests
from aion_brain.lifecycle.redaction import sensitive_metadata_paths


class LifecycleEvaluator:
    """Evaluate lifecycle state without mutating source records."""

    def __init__(
        self,
        repository: object,
        policy_adapter: object | None,
        *,
        registry_repository: object,
        policy_service: object,
        classifier: object,
        archive_planner: object,
        redaction_planner: object,
        purge_preview_service: object,
        notification_router: object | None = None,
        incident_signal_service: object | None = None,
        audit_sink: object | None = None,
        provenance_service: object | None = None,
        telemetry_service: object | None = None,
        settings: object | None = None,
        actor_context: ActorContext | None = None,
    ) -> None:
        self._repository = repository
        self._policy_adapter = policy_adapter
        self._registry_repository = registry_repository
        self._policy_service = policy_service
        self._classifier = classifier
        self._archive_planner = archive_planner
        self._redaction_planner = redaction_planner
        self._purge_preview_service = purge_preview_service
        self._notification_router = notification_router
        self._incident_signal_service = incident_signal_service
        self._audit_sink = audit_sink
        self._provenance_service = provenance_service
        self._telemetry_service = telemetry_service
        self._settings = settings
        self._actor_context = actor_context or ActorContext()

    def with_actor_context(self, actor_context: ActorContext) -> LifecycleEvaluator:
        return LifecycleEvaluator(
            self._repository,
            self._policy_adapter,
            registry_repository=self._registry_repository,
            policy_service=self._policy_service,
            classifier=self._classifier,
            archive_planner=self._archive_planner,
            redaction_planner=self._redaction_planner,
            purge_preview_service=self._purge_preview_service,
            notification_router=self._notification_router,
            incident_signal_service=self._incident_signal_service,
            audit_sink=self._audit_sink,
            provenance_service=self._provenance_service,
            telemetry_service=self._telemetry_service,
            settings=self._settings,
            actor_context=actor_context,
        )

    def evaluate(self, request: LifecycleEvaluationRequest) -> LifecycleEvaluationRun:
        if self._settings is not None and not bool(
            getattr(self._settings, "lifecycle_enabled", True)
        ):
            raise RuntimeError("lifecycle_disabled")
        authorize(
            self._policy_adapter,
            action_type="lifecycle.evaluate",
            resource_type="lifecycle_evaluation",
            resource_id=request.lifecycle_evaluation_id,
            scope=request.owner_scope,
            trace_id=request.trace_id or self._actor_context.trace_id,
            actor_id=request.actor_id or self._actor_context.actor_id,
            workspace_id=request.workspace_id or self._actor_context.workspace_id,
            risk_level="medium",
            context={
                "mode": request.mode,
                "source_records_mutated": False,
                "hard_delete_allowed": False,
            },
        )
        run_id = request.lifecycle_evaluation_id or f"lifecycle-evaluation-{uuid4().hex}"
        trace_id = request.trace_id or self._actor_context.trace_id
        emit_telemetry(
            self._telemetry_service,
            event_type="lifecycle_evaluation_started",
            node_type="lifecycle",
            node_id=run_id,
            intensity=0.7,
            trace_id=trace_id,
            payload={"mode": request.mode},
        )
        resources = _load_resources(self._registry_repository, request)
        policies = _load_policies(self._policy_service, request)
        policy_by_id = {policy.lifecycle_policy_id: policy for policy in policies}
        classifier = cast(Any, _with_context(self._classifier, self._actor_context))
        archive_planner = cast(Any, _with_context(self._archive_planner, self._actor_context))
        redaction_planner = cast(Any, _with_context(self._redaction_planner, self._actor_context))
        purge_preview = cast(Any, _with_context(self._purge_preview_service, self._actor_context))
        classifications: list[RetentionClassification] = []
        archives: list[ArchiveCandidate] = []
        redactions: list[RedactionCandidate] = []
        previews: list[PurgePreview] = []
        reviews: list[LifecycleReviewRecord] = []
        failures: list[dict[str, object]] = []
        for resource in resources:
            try:
                classification = classifier.classify_resource(
                    resource,
                    policies,
                    created_by=request.created_by or request.actor_id,
                )
                classifications.append(classification)
                matching_policy = _policy_for_classification(classification, policy_by_id, policies)
                if request.include_archive_candidates and _should_archive(
                    classification, matching_policy
                ):
                    archives.append(
                        archive_planner.create_candidate(
                            resource,
                            classification,
                            matching_policy,
                            "Lifecycle policy selected this resource for archive review.",
                            persist=request.mode == "controlled",
                        )
                    )
                paths = sensitive_metadata_paths(resource.metadata)
                if request.include_redaction_candidates and (
                    paths or _should_redact(matching_policy)
                ):
                    redactions.append(
                        redaction_planner.create_candidate(
                            resource,
                            classification,
                            "Sensitive metadata path requires lifecycle review.",
                            paths,
                            persist=request.mode == "controlled",
                        )
                    )
                if request.include_purge_previews and _should_preview_purge(
                    classification, matching_policy
                ):
                    previews.append(
                        purge_preview.create_preview(
                            [resource.resource_uri],
                            resource.owner_scope,
                            trace_id=trace_id,
                            created_by=request.created_by or request.actor_id,
                            persist=request.mode == "controlled",
                        )
                    )
                if classification.lifecycle_state == "review_due":
                    reviews.append(
                        LifecycleReviewRecord(
                            lifecycle_review_id=f"lifecycle-review-{uuid4().hex}",
                            trace_id=trace_id,
                            resource_uri=resource.resource_uri,
                            candidate_type="classification",
                            candidate_id=classification.classification_id,
                            status="recorded",
                            decision="manual_review",
                            actor_id=request.actor_id or self._actor_context.actor_id,
                            workspace_id=request.workspace_id or self._actor_context.workspace_id,
                            reason="Lifecycle review due.",
                            owner_scope=resource.owner_scope,
                            metadata={"executed": False},
                            created_by=request.created_by or self._actor_context.actor_id,
                            created_at=datetime.now(UTC),
                        )
                    )
            except Exception as exc:
                failures.append(
                    {"resource_uri": resource.resource_uri, "reason": exc.__class__.__name__}
                )
        if request.mode == "controlled":
            for classification in classifications:
                _save_classification(self._repository, classification)
            for review in reviews:
                _save_review(self._repository, review)
        status = "dry_run" if request.mode == "dry_run" else "completed"
        if failures:
            status = "warning"
        now = datetime.now(UTC)
        run = LifecycleEvaluationRun(
            lifecycle_evaluation_id=run_id,
            trace_id=trace_id,
            actor_id=request.actor_id or self._actor_context.actor_id,
            workspace_id=request.workspace_id or self._actor_context.workspace_id,
            status=cast(LifecycleRunStatus, status),
            mode=request.mode,
            owner_scope=request.owner_scope,
            resource_types=request.resource_types,
            source_systems=request.source_systems,
            policy_ids=[policy.lifecycle_policy_id for policy in policies],
            resources_evaluated=len(resources),
            classifications_created=len(classifications),
            archive_candidates_created=len(archives),
            redaction_candidates_created=len(redactions),
            purge_previews_created=len(previews),
            reviews_created=len(reviews),
            classifications=classifications,
            archive_candidates=archives,
            redaction_candidates=redactions,
            purge_previews=previews,
            review_records=reviews,
            warnings=[],
            failures=failures,
            result={
                "source_records_mutated": False,
                "hard_delete_allowed": False,
                "archive_executed": False,
                "redaction_executed": False,
                "purge_executed": False,
            },
            metadata=request.metadata,
            created_by=request.created_by or self._actor_context.actor_id,
            created_at=now,
            completed_at=now,
        )
        stored = _save_run(self._repository, run)
        self._maybe_notify(request, stored)
        self._maybe_create_incident(request, stored)
        self._record_audit(stored)
        emit_telemetry(
            self._telemetry_service,
            event_type="lifecycle_evaluation_completed",
            node_type="lifecycle",
            node_id=stored.lifecycle_evaluation_id,
            intensity=1.0 if stored.status == "failed" else 0.8,
            trace_id=stored.trace_id,
            payload={
                "status": stored.status,
                "resources_evaluated": stored.resources_evaluated,
            },
        )
        return stored

    def get_evaluation(
        self, lifecycle_evaluation_id: str, scope: list[str]
    ) -> LifecycleEvaluationRun | None:
        authorize(
            self._policy_adapter,
            action_type="lifecycle.evaluate",
            resource_type="lifecycle_evaluation",
            resource_id=lifecycle_evaluation_id,
            scope=scope,
            actor_id=self._actor_context.actor_id,
            workspace_id=self._actor_context.workspace_id,
            risk_level="low",
        )
        get = getattr(self._repository, "get_evaluation_run", None)
        run = get(lifecycle_evaluation_id) if callable(get) else None
        if not isinstance(run, LifecycleEvaluationRun):
            return None
        return run if set(run.owner_scope).intersection(scope) else None

    def _maybe_notify(
        self,
        request: LifecycleEvaluationRequest,
        run: LifecycleEvaluationRun,
    ) -> None:
        should_notify = request.create_notifications or bool(
            getattr(self._settings, "lifecycle_create_notifications_default", False)
        )
        publish = getattr(self._notification_router, "publish", None)
        if not should_notify or not callable(publish):
            return
        try:
            publish(
                NotificationPublishRequest(
                    trace_id=run.trace_id,
                    actor_id=run.actor_id,
                    workspace_id=run.workspace_id,
                    topic_key="lifecycle.evaluation",
                    severity="medium",
                    title="Lifecycle evaluation completed",
                    message="A local lifecycle evaluation completed.",
                    source_type="generic",
                    source_id=run.lifecycle_evaluation_id,
                    owner_scope=run.owner_scope,
                    refs=[run.lifecycle_evaluation_id],
                    metadata={"resources_evaluated": run.resources_evaluated},
                    created_by=run.created_by,
                )
            )
        except Exception:
            return

    def _maybe_create_incident(
        self,
        request: LifecycleEvaluationRequest,
        run: LifecycleEvaluationRun,
    ) -> None:
        should_create = request.create_incident_signals or bool(
            getattr(self._settings, "lifecycle_create_incident_signals_default", False)
        )
        create = getattr(self._incident_signal_service, "create_signal", None)
        if not should_create or not callable(create):
            return
        severity: IncidentSeverity = (
            "high" if run.redaction_candidates or run.purge_previews else "medium"
        )
        try:
            create(
                IncidentSignalCreateRequest(
                    trace_id=run.trace_id,
                    actor_id=run.actor_id,
                    workspace_id=run.workspace_id,
                    source_type="generic",
                    source_id=run.lifecycle_evaluation_id,
                    signal_type="generic",
                    severity=severity,
                    title="Lifecycle evaluation finding",
                    summary="A local lifecycle evaluation produced review findings.",
                    owner_scope=run.owner_scope,
                    refs=[run.lifecycle_evaluation_id],
                    metadata={"resources_evaluated": run.resources_evaluated},
                    created_by=run.created_by,
                )
            )
        except Exception:
            return

    def _record_audit(self, run: LifecycleEvaluationRun) -> None:
        record_audit_event(
            self._audit_sink,
            action_type="lifecycle.evaluate",
            resource_type="lifecycle_evaluation",
            resource_id=run.lifecycle_evaluation_id,
            event_type="lifecycle_evaluation_completed",
            outcome=run.status,
            source_component="lifecycle_evaluator",
            actor_id=run.actor_id,
            payload={
                "resources_evaluated": run.resources_evaluated,
                "source_records_mutated": False,
            },
        )
        create_link = getattr(self._provenance_service, "create_link", None)
        if callable(create_link):
            try:
                create_link(run.lifecycle_evaluation_id, "lifecycle_report", "evaluates")
            except Exception:
                return


def _load_resources(
    registry_repository: object,
    request: LifecycleEvaluationRequest,
) -> list[ResourceDescriptor]:
    list_resources = getattr(registry_repository, "list_resources", None)
    if not callable(list_resources):
        return []
    query = ResourceRegistryQuery(
        scope=request.owner_scope,
        resource_type=request.resource_types[0] if len(request.resource_types) == 1 else None,
        source_system=request.source_systems[0] if len(request.source_systems) == 1 else None,
        limit=1000,
    )
    records = list_resources(query)
    resources = [item.descriptor for item in records if hasattr(item, "descriptor")]
    if request.resource_types:
        resources = [item for item in resources if item.resource_type in request.resource_types]
    if request.source_systems:
        resources = [item for item in resources if item.source_system in request.source_systems]
    return resources


def _load_policies(
    policy_service: object,
    request: LifecycleEvaluationRequest,
) -> list[LifecyclePolicy]:
    list_policies = getattr(policy_service, "list_policies", None)
    policies = (
        list_policies(request.owner_scope, status="active", limit=1000)
        if callable(list_policies)
        else []
    )
    if request.policy_ids:
        policies = [
            policy for policy in policies if policy.lifecycle_policy_id in request.policy_ids
        ]
    if policies:
        return [policy for policy in policies if isinstance(policy, LifecyclePolicy)]
    now = datetime.now(UTC)
    return [
        _policy_from_request(item, now)
        for item in default_lifecycle_policy_requests(request.owner_scope)
    ]


def _policy_from_request(request: LifecyclePolicyCreateRequest, now: datetime) -> LifecyclePolicy:
    return LifecyclePolicy(
        lifecycle_policy_id=request.lifecycle_policy_id or f"lifecycle-policy-{uuid4().hex}",
        name=request.name,
        description=request.description,
        status="active",
        policy_type=request.policy_type,
        resource_types=request.resource_types,
        source_systems=request.source_systems,
        retention_class=request.retention_class,
        retention_days=request.retention_days,
        review_after_days=request.review_after_days,
        archive_after_days=request.archive_after_days,
        purge_after_days=request.purge_after_days,
        action_on_match=request.action_on_match,
        requires_backup=request.requires_backup,
        requires_approval=request.requires_approval,
        owner_scope=request.owner_scope,
        rule=request.rule,
        metadata={**request.metadata, "default_policy": True},
        created_by=request.created_by,
        created_at=now,
        updated_at=now,
    )


def _policy_for_classification(
    classification: RetentionClassification,
    policy_by_id: dict[str, LifecyclePolicy],
    policies: list[LifecyclePolicy],
) -> LifecyclePolicy:
    for policy_id in classification.policy_refs:
        if policy_id in policy_by_id:
            return policy_by_id[policy_id]
    for policy in policies:
        if policy.retention_class in {classification.retention_class, "unknown"}:
            return policy
    return policies[0]


def _should_archive(classification: RetentionClassification, policy: LifecyclePolicy) -> bool:
    return (
        classification.lifecycle_state == "archive_candidate"
        or policy.action_on_match == "create_archive_candidate"
    )


def _should_redact(policy: LifecyclePolicy) -> bool:
    return policy.action_on_match == "create_redaction_candidate"


def _should_preview_purge(classification: RetentionClassification, policy: LifecyclePolicy) -> bool:
    return (
        classification.lifecycle_state == "purge_preview"
        or policy.action_on_match == "create_purge_preview"
    )


def _with_context(service: object, actor_context: ActorContext) -> object:
    with_context = getattr(service, "with_actor_context", None)
    return with_context(actor_context) if callable(with_context) else service


def _save_classification(
    repository: object, classification: RetentionClassification
) -> RetentionClassification:
    save = getattr(repository, "save_classification", None)
    stored = save(classification) if callable(save) else classification
    return stored if isinstance(stored, RetentionClassification) else classification


def _save_review(repository: object, review: LifecycleReviewRecord) -> LifecycleReviewRecord:
    save = getattr(repository, "save_review", None)
    stored = save(review) if callable(save) else review
    return stored if isinstance(stored, LifecycleReviewRecord) else review


def _save_run(repository: object, run: LifecycleEvaluationRun) -> LifecycleEvaluationRun:
    save = getattr(repository, "save_evaluation_run", None)
    stored = save(run) if callable(save) else run
    return stored if isinstance(stored, LifecycleEvaluationRun) else run


__all__ = ["LifecycleEvaluator"]
