"""Pure AION-241 staging qualification validation service."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from aion_brain.contracts.v02_staging_qualification import (
    AUTHORIZATION_TRANSACTION_ID,
    CANDIDATE_ID,
    InMemoryV02StagingQualificationRepository,
    V02StagingArtifactManifest,
    V02StagingArtifactProvenanceRecord,
    V02StagingBuildPlan,
    V02StagingCleanupPlan,
    V02StagingCleanupResult,
    V02StagingDeploymentPlan,
    V02StagingDeploymentResult,
    V02StagingDockerContextProjection,
    V02StagingEnvironmentProfile,
    V02StagingHealthReadinessReport,
    V02StagingIdentityFixtureResult,
    V02StagingIntegrityAudit,
    V02StagingLocalImageInventory,
    V02StagingObservabilitySnapshot,
    V02StagingQualificationAuthorizationEnvelope,
    V02StagingQualificationComponentBinding,
    V02StagingQualificationEvidenceBundle,
    V02StagingQualificationSession,
    V02StagingQualificationSessionPlan,
    V02StagingReplayFixtureResult,
    V02StagingReproducibilityComparison,
    V02StagingRollbackPlan,
    V02StagingRollbackResult,
    V02StagingSecurityValidationReport,
    V02StagingSoftwareBillOfMaterials,
    V02StagingSourceSnapshotManifest,
    V02StagingSourceSnapshotPlan,
    canonical_authorization_envelope,
    canonical_component_binding,
    canonical_evidence_bundle,
    canonical_session_plan,
    v02_staging_fingerprint,
)


class ControlledV02StagingQualificationService:
    """In-memory, effect-free validator for AION-241 evidence supplied by a runner."""

    def __init__(
        self,
        repository: InMemoryV02StagingQualificationRepository | None = None,
    ) -> None:
        self.repository = repository or InMemoryV02StagingQualificationRepository()

    def validate_authorization(
        self,
        envelope: V02StagingQualificationAuthorizationEnvelope,
    ) -> V02StagingQualificationAuthorizationEnvelope:
        if envelope.authorization_transaction_id != AUTHORIZATION_TRANSACTION_ID:
            raise ValueError("unexpected staging qualification authorization")
        if envelope.candidate_id != CANDIDATE_ID:
            raise ValueError("unexpected staging qualification candidate")
        return envelope

    def bind_qualification_foundation(
        self,
        binding: V02StagingQualificationComponentBinding,
    ) -> V02StagingQualificationComponentBinding:
        if binding.authorization_transaction_id != AUTHORIZATION_TRANSACTION_ID:
            raise ValueError("staging binding uses unexpected authorization")
        if binding.production_effect or binding.release_effect:
            raise ValueError("staging binding must be effect-free")
        return binding

    def create_session_plan(
        self,
        session_id: str,
        *,
        now: datetime | None = None,
    ) -> V02StagingQualificationSessionPlan:
        created = now or datetime.now(UTC)
        return canonical_session_plan(
            session_id=session_id,
            created_at=created,
            expires_at=created + timedelta(hours=3),
        )

    def start_session(
        self,
        session_plan: V02StagingQualificationSessionPlan,
    ) -> V02StagingQualificationSession:
        session = V02StagingQualificationSession(
            session_id=session_plan.session_id,
            session_plan_fingerprint=session_plan.session_plan_fingerprint or "",
        )
        self.repository.start_session(session)
        return session

    def validate_source_snapshot(
        self,
        snapshot: V02StagingSourceSnapshotManifest,
    ) -> V02StagingSourceSnapshotManifest:
        if not snapshot.source_snapshot_read_only:
            raise ValueError("source snapshot must be read-only")
        return snapshot

    def validate_source_snapshot_plan(
        self,
        plan: V02StagingSourceSnapshotPlan,
    ) -> V02StagingSourceSnapshotPlan:
        if not plan.read_only_git_archive or plan.source_mutation_allowed:
            raise ValueError("source snapshot plan violates read-only boundary")
        return plan

    def validate_docker_context_projection(
        self,
        projection: V02StagingDockerContextProjection,
    ) -> V02StagingDockerContextProjection:
        if projection.remote_context or projection.docker_host_set:
            raise ValueError("remote Docker contexts are prohibited")
        return projection

    def validate_local_image_inventory(
        self,
        inventory: V02StagingLocalImageInventory,
    ) -> V02StagingLocalImageInventory:
        if inventory.registry_logins or inventory.registry_pulls or inventory.registry_pushes:
            raise ValueError("registry operations are prohibited")
        return inventory

    def validate_build_plan(self, plan: V02StagingBuildPlan) -> V02StagingBuildPlan:
        if plan.network_mode != "none" or plan.pull_policy != "false":
            raise ValueError("staging builds must use network=none and pull=false")
        return plan

    def validate_artifact_manifest(
        self,
        manifest: V02StagingArtifactManifest,
    ) -> V02StagingArtifactManifest:
        if manifest.release_candidate or manifest.production:
            raise ValueError("staging artifact cannot be production or a release candidate")
        return manifest

    def validate_sbom(
        self,
        sbom: V02StagingSoftwareBillOfMaterials,
    ) -> V02StagingSoftwareBillOfMaterials:
        if sbom.registry_called or sbom.final_release_sbom:
            raise ValueError("staging SBOM must remain local and provisional")
        return sbom

    def validate_provenance(
        self,
        provenance: V02StagingArtifactProvenanceRecord,
    ) -> V02StagingArtifactProvenanceRecord:
        if provenance.network_mode != "none" or provenance.pull_policy != "false":
            raise ValueError("provenance must bind the offline build policy")
        return provenance

    def validate_reproducibility_comparison(
        self,
        comparison: V02StagingReproducibilityComparison,
    ) -> V02StagingReproducibilityComparison:
        if not comparison.reproducibility_invariants_passed:
            raise ValueError("reproducibility invariants failed")
        return comparison

    def validate_environment_profile(
        self,
        profile: V02StagingEnvironmentProfile,
    ) -> V02StagingEnvironmentProfile:
        if profile.loopback_host != "127.0.0.1" or not profile.internal_network:
            raise ValueError("staging environment must be loopback-only and internal")
        return profile

    def validate_identity_fixture(
        self,
        result: V02StagingIdentityFixtureResult,
    ) -> V02StagingIdentityFixtureResult:
        if result.private_key_persisted or result.production_identity:
            raise ValueError("identity fixture must remain ephemeral and non-production")
        return result

    def validate_replay_fixture(
        self,
        result: V02StagingReplayFixtureResult,
    ) -> V02StagingReplayFixtureResult:
        if result.persistent_files or result.database_writes:
            raise ValueError("replay fixture must remain ephemeral")
        return result

    def validate_deployment_plan(
        self,
        plan: V02StagingDeploymentPlan,
    ) -> V02StagingDeploymentPlan:
        if plan.dependency_host_ports or plan.pull_policy != "never":
            raise ValueError("deployment plan violates local staging boundary")
        return plan

    def validate_deployment_result(
        self,
        result: V02StagingDeploymentResult,
    ) -> V02StagingDeploymentResult:
        if result.public_listeners_created or result.non_loopback_listeners_created:
            raise ValueError("deployment created non-loopback exposure")
        return result

    def validate_health_readiness(
        self,
        report: V02StagingHealthReadinessReport,
    ) -> V02StagingHealthReadinessReport:
        if not report.all_dependencies_ready:
            raise ValueError("staging readiness did not pass")
        return report

    def validate_security_validation(
        self,
        report: V02StagingSecurityValidationReport,
    ) -> V02StagingSecurityValidationReport:
        if report.security_tests_passed < 8:
            raise ValueError("insufficient staging security scenarios")
        return report

    def validate_observability(
        self,
        snapshot: V02StagingObservabilitySnapshot,
    ) -> V02StagingObservabilitySnapshot:
        if snapshot.external_log_exports or snapshot.external_metric_exports:
            raise ValueError("observability export is prohibited")
        return snapshot

    def validate_rollback_plan(
        self,
        plan: V02StagingRollbackPlan,
    ) -> V02StagingRollbackPlan:
        if plan.production_rollback:
            raise ValueError("AION-241 rollback is staging-only")
        return plan

    def validate_rollback_result(
        self,
        result: V02StagingRollbackResult,
    ) -> V02StagingRollbackResult:
        if not result.post_rollback_health_recovered or result.production_effect:
            raise ValueError("rollback did not recover safely")
        return result

    def validate_cleanup_plan(self, plan: V02StagingCleanupPlan) -> V02StagingCleanupPlan:
        if not plan.preserves_pre_existing_resources:
            raise ValueError("cleanup must preserve pre-existing resources")
        return plan

    def validate_cleanup_result(
        self,
        result: V02StagingCleanupResult,
    ) -> V02StagingCleanupResult:
        if result.active_run_owned_containers or result.active_run_owned_images:
            raise ValueError("cleanup left run-owned resources")
        return result

    def audit_integrity(
        self,
        audit: V02StagingIntegrityAudit,
    ) -> V02StagingIntegrityAudit:
        if not audit.zero_effects_passed or not audit.cleanup_passed:
            raise ValueError("integrity audit failed")
        return audit

    def create_evidence_bundle(
        self,
        bundle: V02StagingQualificationEvidenceBundle,
    ) -> V02StagingQualificationEvidenceBundle:
        if not bundle.integrity_passed or bundle.production_effect or bundle.release_effect:
            raise ValueError("staging evidence violates integrity or effect boundary")
        request_fingerprint = v02_staging_fingerprint(
            {
                "authorization_id": bundle.authorization_id,
                "implementation_commit": bundle.implementation_commit,
                "pilot_id": bundle.pilot_id,
                "report_fingerprint": bundle.report_fingerprint,
            }
        )
        self.repository.record_evidence(bundle, request_fingerprint)
        return bundle

    def replay_exact_qualification(
        self,
        pilot_id: str,
        request_fingerprint: str,
    ) -> V02StagingQualificationEvidenceBundle:
        return self.repository.replay_exact_qualification(pilot_id, request_fingerprint)

    def reject_changed_replay(self, pilot_id: str) -> bool:
        try:
            self.repository.replay_exact_qualification(
                pilot_id,
                v02_staging_fingerprint({"pilot_id": pilot_id, "changed": True}),
            )
        except ValueError:
            return True
        return False

    def close_session(self, session_id: str) -> V02StagingQualificationSession:
        return self.repository.close_session(session_id)

    def run_canonical_pilot_projection(self) -> V02StagingQualificationEvidenceBundle:
        binding = canonical_component_binding()
        self.validate_authorization(canonical_authorization_envelope(binding))
        bundle = canonical_evidence_bundle()
        return self.create_evidence_bundle(bundle)


__all__ = ["ControlledV02StagingQualificationService"]
