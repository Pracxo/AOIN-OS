"""Disabled local release-qualification service."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

from aion_brain.contracts.v02_release_qualification import (
    AUTHORIZATION_TRANSACTION_ID,
    CANDIDATE_ID,
    CANONICAL_RELEASE_GATE_IDS,
    FOUNDATION_DECISION,
    PILOT_ID,
    PROHIBITED_EFFECT_COUNTERS,
    READINESS_DOMAINS,
    InMemoryV02QualificationRepository,
    V02ArtifactProvenanceRecord,
    V02CredentialLifecyclePolicy,
    V02DeploymentArtifactManifest,
    V02IdentityProviderAdapterManifest,
    V02IntegrityStatus,
    V02ProductionAuthCompositionPlan,
    V02ProductionHealthReadinessSchema,
    V02ProductionObservabilitySchema,
    V02ProductionReadinessGapMatrix,
    V02ProductionThreatModel,
    V02ProtectedMaterialLifecyclePolicy,
    V02PublicKeyLifecyclePolicy,
    V02QualificationFoundationDecision,
    V02QualificationIntegrityAudit,
    V02QualificationRunResult,
    V02QualificationSession,
    V02QualificationSessionPlan,
    V02ReleaseGateMatrix,
    V02ReleaseQualificationAuthorizationEnvelope,
    V02ReleaseQualificationComponentBinding,
    V02ReplayLedgerProvisioningPlan,
    V02ReproducibleBuildEvidenceProjection,
    V02RollbackDrillPlan,
    V02RollbackDrillSimulationResult,
    V02RollbackPlan,
    V02RuntimeGuardOutcome,
    V02RuntimeReleaseGuardDecision,
    V02SessionLifecyclePolicy,
    V02SoftwareBillOfMaterialsProjection,
    V02StagingQualificationPlan,
    V02TokenLifecyclePolicy,
    V02VerifiedRequestIdentityIntegrationPlan,
    canonical_authorization_envelope,
    canonical_component_binding,
    canonical_credential_policies,
    canonical_deployment_manifests,
    canonical_gap_matrix,
    canonical_health_readiness_schema,
    canonical_identity_provider_manifests,
    canonical_key_policies,
    canonical_observability_schema,
    canonical_production_auth_composition,
    canonical_protected_material_policy,
    canonical_provenance_records,
    canonical_release_gate_matrix,
    canonical_replay_provisioning_plan,
    canonical_reproducibility_projections,
    canonical_request_identity_plan,
    canonical_rollback_drill_plan,
    canonical_rollback_plans,
    canonical_sbom_projection,
    canonical_session_plan,
    canonical_session_policies,
    canonical_staging_plan,
    canonical_threat_model,
    canonical_token_policies,
    v02_qualification_fingerprint,
)


class ControlledV02ReleaseQualificationService:
    """In-memory, disabled v0.2 production-readiness qualification service."""

    def __init__(self, repository: InMemoryV02QualificationRepository | None = None) -> None:
        self.repository = repository or InMemoryV02QualificationRepository()

    def validate_authorization(
        self,
        envelope: V02ReleaseQualificationAuthorizationEnvelope,
    ) -> V02ReleaseQualificationAuthorizationEnvelope:
        if envelope.authorization_transaction_id != AUTHORIZATION_TRANSACTION_ID:
            raise ValueError("unexpected v0.2 qualification authorization")
        if envelope.candidate_id != CANDIDATE_ID:
            raise ValueError("unexpected v0.2 qualification candidate")
        if tuple(envelope.allowed_readiness_domains) != READINESS_DOMAINS:
            raise ValueError("authorization must cover all readiness domains")
        if tuple(envelope.required_release_gate_ids) != CANONICAL_RELEASE_GATE_IDS:
            raise ValueError("authorization must bind all release gates")
        required_false = (
            envelope.production_auth,
            envelope.external_idp,
            envelope.credential_effect,
            envelope.token_effect,
            envelope.database_effect,
            envelope.deployment_effect,
            envelope.release_effect,
            envelope.authorization_consumed,
            envelope.authorization_expired,
            envelope.authorization_reusable,
        )
        if any(required_false) or not envelope.authorization_active:
            raise ValueError("authorization must remain active, disabled and single-use")
        return envelope

    def bind_parent_program(
        self,
        binding: V02ReleaseQualificationComponentBinding,
    ) -> V02ReleaseQualificationComponentBinding:
        if binding.authorization_transaction_id != AUTHORIZATION_TRANSACTION_ID:
            raise ValueError("parent binding uses unexpected authorization")
        if not binding.read_only or not binding.redacted:
            raise ValueError("parent binding must be read-only and redacted")
        if binding.production_effect or binding.runtime_effect:
            raise ValueError("parent binding must not create effects")
        return binding

    def create_session_plan(
        self,
        session_id: str,
        *,
        now: datetime | None = None,
    ) -> V02QualificationSessionPlan:
        created = now or datetime.now(UTC)
        return canonical_session_plan(
            session_id,
            created_at=created,
            expires_at=created + timedelta(minutes=45),
        )

    def start_session(
        self,
        session_plan: V02QualificationSessionPlan,
    ) -> V02QualificationSession:
        session = V02QualificationSession(
            session_id=session_plan.session_id,
            session_plan_fingerprint=session_plan.session_plan_fingerprint or "",
            candidate_references_loaded=True,
            evidence_references_loaded=True,
        )
        self.repository.start_session(session)
        return session

    def load_gap_matrix(self) -> V02ProductionReadinessGapMatrix:
        return canonical_gap_matrix()

    def validate_gap_matrix(
        self,
        matrix: V02ProductionReadinessGapMatrix,
    ) -> V02ProductionReadinessGapMatrix:
        if len(matrix.gaps) != 20:
            raise ValueError("gap matrix must evaluate 20 readiness gaps")
        if tuple(matrix.readiness_domains_represented) != READINESS_DOMAINS:
            raise ValueError("gap matrix must represent all readiness domains")
        if not matrix.staging_evidence_required or not matrix.production_evidence_required:
            raise ValueError("AION-239 must leave staging and production evidence unresolved")
        return matrix

    def validate_production_auth_composition(
        self,
        plan: V02ProductionAuthCompositionPlan,
    ) -> V02ProductionAuthCompositionPlan:
        if plan.production_auth_runtime_enabled or plan.external_identity_provider_call_enabled:
            raise ValueError("production auth composition must remain disabled")
        if plan.live_key_rotation_enabled or plan.live_replay_ledger_enabled:
            raise ValueError("live key rotation and replay ledger writes are disabled")
        return plan

    def validate_request_identity_plan(
        self,
        plan: V02VerifiedRequestIdentityIntegrationPlan,
    ) -> V02VerifiedRequestIdentityIntegrationPlan:
        if plan.browser_headers_create_identity or plan.cookies_create_identity:
            raise ValueError("unverified browser data cannot create identity")
        if plan.raw_claims_retained:
            raise ValueError("raw claims must not be retained")
        return plan

    def validate_replay_provisioning_plan(
        self,
        plan: V02ReplayLedgerProvisioningPlan,
    ) -> V02ReplayLedgerProvisioningPlan:
        if plan.live_replay_ledger_enabled or plan.production_database_provisioning_enabled:
            raise ValueError("replay provisioning is design-only")
        if plan.maximum_live_replay_ledger_writes or plan.maximum_production_database_operations:
            raise ValueError("replay and database effect budgets must remain zero")
        return plan

    def validate_identity_provider_manifests(
        self,
        manifests: tuple[V02IdentityProviderAdapterManifest, ...],
    ) -> tuple[V02IdentityProviderAdapterManifest, ...]:
        if not manifests:
            raise ValueError("at least one disabled IdP manifest is required")
        for manifest in manifests:
            if (
                manifest.connect_available
                or manifest.authorize_available
                or manifest.exchange_code_available
                or manifest.refresh_available
                or manifest.fetch_metadata_available
                or manifest.fetch_keys_available
                or manifest.load_client_secret_available
                or manifest.create_authorization_header_available
                or manifest.external_identity_provider_call_enabled
                or manifest.maximum_external_identity_provider_calls
            ):
                raise ValueError("IdP adapter manifest exposes a live operation")
        return manifests

    def validate_key_lifecycle_policies(
        self,
        policies: tuple[V02PublicKeyLifecyclePolicy, ...],
    ) -> tuple[V02PublicKeyLifecyclePolicy, ...]:
        for policy in policies:
            if policy.private_key_material_present or policy.public_key_bytes_present:
                raise ValueError("key lifecycle evidence cannot contain key material")
            if policy.live_key_rotation_enabled or policy.maximum_live_key_rotations:
                raise ValueError("live key rotation is disabled")
        return policies

    def validate_protected_material_policies(
        self,
        policy: V02ProtectedMaterialLifecyclePolicy,
    ) -> V02ProtectedMaterialLifecyclePolicy:
        if policy.protected_value_stored:
            raise ValueError("protected values must not be stored")
        if len(policy.classes) < 10:
            raise ValueError("protected material policy must classify at least ten classes")
        return policy

    def validate_credential_lifecycle_policies(
        self,
        policies: tuple[V02CredentialLifecyclePolicy, ...],
    ) -> tuple[V02CredentialLifecyclePolicy, ...]:
        for policy in policies:
            if (
                policy.credentials_generated
                or policy.credentials_read
                or policy.credentials_persisted
            ):
                raise ValueError("credential lifecycle policy must not create effects")
        return policies

    def validate_token_lifecycle_policies(
        self,
        policies: tuple[V02TokenLifecyclePolicy, ...],
    ) -> tuple[V02TokenLifecyclePolicy, ...]:
        for policy in policies:
            if (
                policy.tokens_generated
                or policy.tokens_read
                or policy.tokens_persisted
                or policy.session_tokens_issued
                or policy.access_tokens_issued
                or policy.refresh_tokens_issued
            ):
                raise ValueError("token lifecycle policy must not issue or store tokens")
        return policies

    def validate_session_lifecycle_policies(
        self,
        policies: tuple[V02SessionLifecyclePolicy, ...],
    ) -> tuple[V02SessionLifecyclePolicy, ...]:
        for policy in policies:
            if policy.session_tokens_issued:
                raise ValueError("session lifecycle policy must not issue session tokens")
        return policies

    def validate_deployment_artifact_manifests(
        self,
        manifests: tuple[V02DeploymentArtifactManifest, ...],
    ) -> tuple[V02DeploymentArtifactManifest, ...]:
        for manifest in manifests:
            if (
                manifest.artifact_bytes_present
                or manifest.artifact_built
                or manifest.artifact_pushed
                or manifest.release_candidate
            ):
                raise ValueError("deployment artifact manifest must remain a projection")
        return manifests

    def validate_sbom_projection(
        self,
        projection: V02SoftwareBillOfMaterialsProjection,
    ) -> V02SoftwareBillOfMaterialsProjection:
        if projection.private_registry_credentials_present:
            raise ValueError("SBOM projection must not contain registry credentials")
        if len(projection.components) < 12:
            raise ValueError("SBOM projection must include at least twelve components")
        return projection

    def validate_artifact_provenance(
        self,
        records: tuple[V02ArtifactProvenanceRecord, ...],
    ) -> tuple[V02ArtifactProvenanceRecord, ...]:
        if len(records) < 4:
            raise ValueError("artifact provenance requires at least four records")
        if any(record.artifact_bytes_present for record in records):
            raise ValueError("artifact provenance must not retain artifact bytes")
        return records

    def validate_reproducibility_projection(
        self,
        projections: tuple[V02ReproducibleBuildEvidenceProjection, ...],
    ) -> tuple[V02ReproducibleBuildEvidenceProjection, ...]:
        for projection in projections:
            if (
                projection.actual_build_executed
                or projection.actual_artifact_created
                or projection.reproducible_build_claimed_passed
            ):
                raise ValueError("reproducibility remains a deterministic projection")
        return projections

    def validate_rollback_plans(
        self,
        plans: tuple[V02RollbackPlan, ...],
    ) -> tuple[V02RollbackPlan, ...]:
        for plan in plans:
            if plan.rollback_execution_enabled or plan.maximum_rollback_executions:
                raise ValueError("rollback execution is disabled")
            if any(step.command_present for step in plan.steps):
                raise ValueError("rollback plan must not contain executable commands")
        return plans

    def simulate_rollback_drill(
        self,
        drill_plan: V02RollbackDrillPlan,
    ) -> V02RollbackDrillSimulationResult:
        if (
            drill_plan.execute_commands
            or drill_plan.mutate_database
            or drill_plan.replace_artifact
            or drill_plan.change_configuration
            or drill_plan.restart_service
            or drill_plan.deploy
        ):
            raise ValueError("rollback drill simulator must not execute operational steps")
        return V02RollbackDrillSimulationResult(
            drill_id=drill_plan.drill_id,
            rollback_plan_ids=drill_plan.rollback_plan_ids,
            dependencies_valid=True,
            preconditions_valid=True,
            health_checks_referenced=True,
            evidence_requirements_valid=True,
        )

    def validate_observability_schema(
        self,
        schema: V02ProductionObservabilitySchema,
    ) -> V02ProductionObservabilitySchema:
        if (
            schema.production_observability_export_enabled
            or schema.external_log_export_enabled
            or schema.external_metric_export_enabled
            or schema.external_trace_export_enabled
        ):
            raise ValueError("observability exporters are not implemented")
        if len(schema.signals) < 24:
            raise ValueError("observability schema must define at least 24 signals")
        return schema

    def validate_health_readiness_schema(
        self,
        schema: V02ProductionHealthReadinessSchema,
    ) -> V02ProductionHealthReadinessSchema:
        if len(schema.checks) < 12:
            raise ValueError("health readiness schema must define at least 12 checks")
        return schema

    def validate_threat_model(
        self,
        threat_model: V02ProductionThreatModel,
    ) -> V02ProductionThreatModel:
        if threat_model.exploit_code_present or threat_model.operational_secrets_present:
            raise ValueError("threat model must not retain exploit code or secrets")
        if len(threat_model.scenarios) < 40:
            raise ValueError("threat model must cover at least 40 scenarios")
        return threat_model

    def evaluate_runtime_guard(
        self,
        *,
        gap_matrix: V02ProductionReadinessGapMatrix,
        release_gate_matrix: V02ReleaseGateMatrix,
    ) -> V02RuntimeReleaseGuardDecision:
        if not gap_matrix.staging_evidence_required or release_gate_matrix.v02_release_ready:
            raise ValueError("runtime guard cannot mark v0.2 release ready")
        return V02RuntimeReleaseGuardDecision(
            outcome=V02RuntimeGuardOutcome.allow_disabled_qualification,
            qualification_decision=(
                V02QualificationFoundationDecision
                .foundation_implemented_release_not_ready_staging_evidence_required
            ),
        )

    def evaluate_release_gates(
        self,
        matrix: V02ReleaseGateMatrix,
    ) -> V02ReleaseGateMatrix:
        if len(matrix.gates) != 24 or matrix.v02_release_ready:
            raise ValueError("release gate matrix must preserve release hold")
        if matrix.v02_release_candidate_created:
            raise ValueError("release candidate creation is not authorized")
        return matrix

    def validate_staging_qualification_plan(
        self,
        plan: V02StagingQualificationPlan,
    ) -> V02StagingQualificationPlan:
        if plan.staging_runtime_authorized or plan.staging_deployment_enabled:
            raise ValueError("staging qualification plan remains design-only")
        if plan.maximum_staging_deployments:
            raise ValueError("staging deployment budget must remain zero")
        return plan

    def create_qualification_report(
        self,
        *,
        run_id: str,
        component_binding: V02ReleaseQualificationComponentBinding,
        authorization_envelope: V02ReleaseQualificationAuthorizationEnvelope,
        qualification_candidate_fingerprint: str,
        gap_matrix: V02ProductionReadinessGapMatrix,
        production_auth_composition: V02ProductionAuthCompositionPlan,
        request_identity_plan: V02VerifiedRequestIdentityIntegrationPlan,
        replay_provisioning_plan: V02ReplayLedgerProvisioningPlan,
        identity_provider_manifests: tuple[V02IdentityProviderAdapterManifest, ...],
        key_policies: tuple[V02PublicKeyLifecyclePolicy, ...],
        protected_material_policy: V02ProtectedMaterialLifecyclePolicy,
        credential_policies: tuple[V02CredentialLifecyclePolicy, ...],
        token_policies: tuple[V02TokenLifecyclePolicy, ...],
        session_policies: tuple[V02SessionLifecyclePolicy, ...],
        deployment_manifests: tuple[V02DeploymentArtifactManifest, ...],
        sbom_projection: V02SoftwareBillOfMaterialsProjection,
        provenance_records: tuple[V02ArtifactProvenanceRecord, ...],
        reproducibility_projections: tuple[V02ReproducibleBuildEvidenceProjection, ...],
        rollback_plans: tuple[V02RollbackPlan, ...],
        rollback_drill_result: V02RollbackDrillSimulationResult,
        observability_schema: V02ProductionObservabilitySchema,
        health_readiness_schema: V02ProductionHealthReadinessSchema,
        threat_model: V02ProductionThreatModel,
        runtime_guard: V02RuntimeReleaseGuardDecision,
        release_gate_matrix: V02ReleaseGateMatrix,
        staging_plan: V02StagingQualificationPlan,
        request_fingerprint: str,
    ) -> V02QualificationRunResult:
        result = V02QualificationRunResult(
            run_id=run_id,
            component_binding_fingerprint=component_binding.binding_fingerprint or "",
            authorization_envelope_fingerprint=(
                authorization_envelope.envelope_fingerprint or ""
            ),
            qualification_candidate_fingerprint=qualification_candidate_fingerprint,
            gap_matrix_fingerprint=gap_matrix.gap_matrix_fingerprint or "",
            production_auth_composition_fingerprint=(
                production_auth_composition.composition_fingerprint or ""
            ),
            request_identity_plan_fingerprint=(
                request_identity_plan.request_identity_plan_fingerprint or ""
            ),
            replay_provisioning_plan_fingerprint=(
                replay_provisioning_plan.replay_plan_fingerprint or ""
            ),
            identity_provider_manifest_fingerprints=tuple(
                manifest.identity_provider_manifest_fingerprint or ""
                for manifest in identity_provider_manifests
            ),
            public_key_lifecycle_policy_fingerprints=tuple(
                policy.policy_fingerprint or "" for policy in key_policies
            ),
            protected_material_policy_fingerprints=(
                protected_material_policy.policy_fingerprint or "",
            ),
            credential_policy_fingerprints=tuple(
                policy.policy_fingerprint or "" for policy in credential_policies
            ),
            token_policy_fingerprints=tuple(
                policy.policy_fingerprint or "" for policy in token_policies
            ),
            session_policy_fingerprints=tuple(
                policy.policy_fingerprint or "" for policy in session_policies
            ),
            deployment_artifact_manifest_fingerprints=tuple(
                manifest.manifest_fingerprint or "" for manifest in deployment_manifests
            ),
            sbom_projection_fingerprint=sbom_projection.sbom_projection_fingerprint or "",
            artifact_provenance_chain_head=(
                provenance_records[-1].provenance_fingerprint or ""
            ),
            reproducibility_projection_fingerprints=tuple(
                projection.projection_fingerprint or ""
                for projection in reproducibility_projections
            ),
            rollback_plan_fingerprints=tuple(
                plan.rollback_plan_fingerprint or "" for plan in rollback_plans
            ),
            rollback_drill_result_fingerprint=(
                rollback_drill_result.drill_result_fingerprint or ""
            ),
            observability_schema_fingerprint=(
                observability_schema.observability_schema_fingerprint or ""
            ),
            health_readiness_schema_fingerprint=(
                health_readiness_schema.health_readiness_schema_fingerprint or ""
            ),
            threat_model_fingerprint=threat_model.threat_model_fingerprint or "",
            runtime_guard_fingerprint=runtime_guard.runtime_guard_fingerprint or "",
            release_gate_matrix_fingerprint=(
                release_gate_matrix.release_gate_matrix_fingerprint or ""
            ),
            staging_plan_fingerprint=staging_plan.staging_plan_fingerprint or "",
            qualification_decision=(
                V02QualificationFoundationDecision
                .foundation_implemented_release_not_ready_staging_evidence_required
            ),
            protected_material_classes_validated=len(protected_material_policy.classes),
            sbom_components_projected=len(sbom_projection.components),
            artifact_provenance_records_validated=len(provenance_records),
            observability_signals_validated=len(observability_schema.signals),
            health_readiness_checks_validated=len(health_readiness_schema.checks),
            threat_scenarios_validated=len(threat_model.scenarios),
            prohibited_effect_counters=dict(PROHIBITED_EFFECT_COUNTERS),
        )
        self.repository.record_run(result, request_fingerprint=request_fingerprint)
        return result

    def audit_integrity(
        self,
        result: V02QualificationRunResult,
    ) -> V02QualificationIntegrityAudit:
        checked = (
            result.component_binding_fingerprint,
            result.authorization_envelope_fingerprint,
            result.gap_matrix_fingerprint,
            result.release_gate_matrix_fingerprint,
            result.report_fingerprint or "",
        )
        return V02QualificationIntegrityAudit(
            integrity_status=V02IntegrityStatus.passed,
            checked_fingerprints=checked,
        )

    def replay_exact_run(
        self,
        run_id: str,
        request_fingerprint: str,
    ) -> V02QualificationRunResult:
        return self.repository.replay_exact_run(run_id, request_fingerprint)

    def reject_changed_replay(self, run_id: str, request_fingerprint: str) -> None:
        try:
            self.repository.replay_exact_run(run_id, request_fingerprint)
        except ValueError:
            return
        raise ValueError("changed replay unexpectedly accepted")

    def close_session(self, session_id: str) -> V02QualificationSession:
        return self.repository.close_session(session_id)

    def run_canonical_disabled_pilot(self) -> V02QualificationRunResult:
        now = datetime(2026, 8, 1, 15, 0, 0, tzinfo=UTC)
        component_binding = self.bind_parent_program(
            canonical_component_binding(binding_timestamp=now)
        )
        session_plan = self.create_session_plan("aion-239-local-session", now=now)
        authorization = self.validate_authorization(
            canonical_authorization_envelope(
                component_binding,
                session_plan.session_id,
                created_at=now,
                expires_at=now + timedelta(minutes=45),
            )
        )
        self.start_session(session_plan)
        gap_matrix = self.validate_gap_matrix(self.load_gap_matrix())
        production_auth = self.validate_production_auth_composition(
            canonical_production_auth_composition()
        )
        request_identity = self.validate_request_identity_plan(
            canonical_request_identity_plan()
        )
        replay_plan = self.validate_replay_provisioning_plan(
            canonical_replay_provisioning_plan()
        )
        idp_manifests = self.validate_identity_provider_manifests(
            canonical_identity_provider_manifests()
        )
        key_policies = self.validate_key_lifecycle_policies(canonical_key_policies())
        protected_material = self.validate_protected_material_policies(
            canonical_protected_material_policy()
        )
        credential_policies = self.validate_credential_lifecycle_policies(
            canonical_credential_policies()
        )
        token_policies = self.validate_token_lifecycle_policies(canonical_token_policies())
        session_policies = self.validate_session_lifecycle_policies(
            canonical_session_policies()
        )
        deployment_manifests = self.validate_deployment_artifact_manifests(
            canonical_deployment_manifests()
        )
        sbom = self.validate_sbom_projection(canonical_sbom_projection())
        provenance = self.validate_artifact_provenance(canonical_provenance_records())
        reproducibility = self.validate_reproducibility_projection(
            canonical_reproducibility_projections()
        )
        rollback_plans = self.validate_rollback_plans(canonical_rollback_plans())
        drill = canonical_rollback_drill_plan(rollback_plans)
        drill_result = self.simulate_rollback_drill(drill)
        observability = self.validate_observability_schema(
            canonical_observability_schema()
        )
        health = self.validate_health_readiness_schema(canonical_health_readiness_schema())
        threats = self.validate_threat_model(canonical_threat_model())
        gates = self.evaluate_release_gates(canonical_release_gate_matrix())
        guard = self.evaluate_runtime_guard(gap_matrix=gap_matrix, release_gate_matrix=gates)
        staging = self.validate_staging_qualification_plan(canonical_staging_plan())
        candidate_fingerprint = v02_qualification_fingerprint(
            {
                "candidate_id": CANDIDATE_ID,
                "pilot_id": PILOT_ID,
                "decision": FOUNDATION_DECISION,
            }
        )
        request_payload: dict[str, Any] = {
            "authorization": authorization.envelope_fingerprint,
            "candidate": candidate_fingerprint,
            "gap_matrix": gap_matrix.gap_matrix_fingerprint,
            "release_gates": gates.release_gate_matrix_fingerprint,
            "staging": staging.staging_plan_fingerprint,
        }
        request_fingerprint = v02_qualification_fingerprint(request_payload)
        self.close_session(session_plan.session_id)
        result = self.create_qualification_report(
            run_id="AION-239-local-run-001",
            component_binding=component_binding,
            authorization_envelope=authorization,
            qualification_candidate_fingerprint=candidate_fingerprint,
            gap_matrix=gap_matrix,
            production_auth_composition=production_auth,
            request_identity_plan=request_identity,
            replay_provisioning_plan=replay_plan,
            identity_provider_manifests=idp_manifests,
            key_policies=key_policies,
            protected_material_policy=protected_material,
            credential_policies=credential_policies,
            token_policies=token_policies,
            session_policies=session_policies,
            deployment_manifests=deployment_manifests,
            sbom_projection=sbom,
            provenance_records=provenance,
            reproducibility_projections=reproducibility,
            rollback_plans=rollback_plans,
            rollback_drill_result=drill_result,
            observability_schema=observability,
            health_readiness_schema=health,
            threat_model=threats,
            runtime_guard=guard,
            release_gate_matrix=gates,
            staging_plan=staging,
            request_fingerprint=request_fingerprint,
        )
        replayed = self.replay_exact_run(result.run_id, request_fingerprint)
        if replayed.report_fingerprint != result.report_fingerprint:
            raise ValueError("exact replay did not return the recorded result")
        changed_request = v02_qualification_fingerprint(
            {**request_payload, "changed_evidence": True}
        )
        self.reject_changed_replay(result.run_id, changed_request)
        self.audit_integrity(result)
        return result


__all__ = ["ControlledV02ReleaseQualificationService"]
