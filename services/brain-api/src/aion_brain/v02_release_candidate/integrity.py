"""Pure AION-243 release-candidate validation service."""

from __future__ import annotations

from datetime import UTC, datetime

from aion_brain.contracts.v02_release_candidate import (
    AUTHORIZATION_TRANSACTION_ID,
    CANDIDATE_LABEL,
    InMemoryV02ReleaseCandidateRepository,
    V02CandidateArtifactManifest,
    V02CandidateArtifactPlan,
    V02CandidateChecksumManifest,
    V02CandidateCompatibilityMatrix,
    V02CandidateEvidenceBundle,
    V02CandidateIntegrityReport,
    V02CandidateMigrationManifest,
    V02CandidateProvenanceChain,
    V02CandidateReleaseNotesRecord,
    V02CandidateReproducibilityComparison,
    V02CandidateRetentionResult,
    V02CandidateSbomDocument,
    V02CandidateSourceSnapshotManifest,
    V02CandidateVersionManifest,
    V02QualificationPublicKeyRecord,
    V02QualificationSignatureRecord,
    V02ReleaseCandidateAuthorizationEnvelope,
    V02ReleaseCandidateComponentBinding,
    V02ReleaseCandidateSession,
    V02ReleaseCandidateSessionPlan,
    canonical_session_plan,
)


class ControlledV02ReleaseCandidateService:
    """Effect-free validator for AION-243 runner-supplied candidate evidence."""

    def __init__(
        self,
        repository: InMemoryV02ReleaseCandidateRepository | None = None,
    ) -> None:
        self.repository = repository or InMemoryV02ReleaseCandidateRepository()

    def validate_authorization(
        self, envelope: V02ReleaseCandidateAuthorizationEnvelope
    ) -> V02ReleaseCandidateAuthorizationEnvelope:
        if envelope.authorization_transaction_id != AUTHORIZATION_TRANSACTION_ID:
            raise ValueError("unexpected release-candidate authorization")
        if envelope.authorization_consumed or envelope.authorization_expired:
            raise ValueError("AION-243 authorization must remain active")
        return envelope

    def bind_staging_evidence(
        self, binding: V02ReleaseCandidateComponentBinding
    ) -> V02ReleaseCandidateComponentBinding:
        if binding.production_effect or binding.publication_effect:
            raise ValueError("component binding must not create production or publication effect")
        return binding

    def create_session_plan(
        self, session_id: str, *, now: datetime | None = None
    ) -> V02ReleaseCandidateSessionPlan:
        return canonical_session_plan(session_id, now=now)

    def start_session(
        self, session_plan: V02ReleaseCandidateSessionPlan
    ) -> V02ReleaseCandidateSession:
        if session_plan.candidate_label != CANDIDATE_LABEL:
            raise ValueError("unexpected candidate label")
        session = V02ReleaseCandidateSession(
            session_id=session_plan.session_id,
            created_at=datetime.now(UTC),
            session_plan_fingerprint=session_plan.session_plan_fingerprint,
        )
        return self.repository.start_session(session)

    def validate_source_snapshot(
        self, snapshot: V02CandidateSourceSnapshotManifest
    ) -> V02CandidateSourceSnapshotManifest:
        if not snapshot.deterministic_archive:
            raise ValueError("source archive must be deterministic")
        return snapshot

    def validate_version_manifest(
        self, manifest: V02CandidateVersionManifest
    ) -> V02CandidateVersionManifest:
        if manifest.dependency_changes or manifest.migration_changes:
            raise ValueError("AION-243 version manifest must be version-only")
        if manifest.git_tag_created or manifest.github_release_created:
            raise ValueError("AION-243 must not create release tags or releases")
        return manifest

    def validate_artifact_plan(self, plan: V02CandidateArtifactPlan) -> V02CandidateArtifactPlan:
        if plan.network_mode != "none" or plan.pull_policy != "false":
            raise ValueError("candidate builds must use network=none and pull=false")
        if plan.registry_login or plan.registry_pull or plan.registry_push or plan.package_upload:
            raise ValueError("candidate build plan must not publish or access registries")
        return plan

    def validate_artifact_manifest(
        self, manifest: V02CandidateArtifactManifest
    ) -> V02CandidateArtifactManifest:
        if manifest.production or manifest.publication:
            raise ValueError("candidate artifact manifest must remain local")
        return manifest

    def validate_sbom(self, sbom: V02CandidateSbomDocument) -> V02CandidateSbomDocument:
        if sbom.registry_called or sbom.vulnerability_scan_completed:
            raise ValueError("candidate SBOM is a local projection, not registry or vuln scan")
        return sbom

    def validate_provenance(
        self, provenance: V02CandidateProvenanceChain
    ) -> V02CandidateProvenanceChain:
        for record in provenance.records:
            if record.network_mode != "none" or record.pull_policy != "false":
                raise ValueError("provenance must bind offline build settings")
            if record.production or record.publication:
                raise ValueError("provenance must not claim production or publication")
        return provenance

    def validate_checksums(
        self, manifest: V02CandidateChecksumManifest
    ) -> V02CandidateChecksumManifest:
        paths = [record.relative_path for record in manifest.records]
        if paths != sorted(paths) or len(paths) != len(set(paths)):
            raise ValueError("checksum paths must be sorted and unique")
        return manifest

    def validate_public_key_record(
        self, record: V02QualificationPublicKeyRecord
    ) -> V02QualificationPublicKeyRecord:
        if not record.qualification_only or record.production_signing_key:
            raise ValueError("public key record must be qualification-only")
        return record

    def validate_signatures(
        self, records: tuple[V02QualificationSignatureRecord, ...]
    ) -> tuple[V02QualificationSignatureRecord, ...]:
        if not records or any(not record.verified for record in records):
            raise ValueError("every detached signature must verify")
        return records

    def validate_reproducibility(
        self, comparison: V02CandidateReproducibilityComparison
    ) -> V02CandidateReproducibilityComparison:
        if not comparison.reproducibility_invariants_passed:
            raise ValueError("candidate reproducibility invariants failed")
        return comparison

    def validate_compatibility(
        self, matrix: V02CandidateCompatibilityMatrix
    ) -> V02CandidateCompatibilityMatrix:
        if not matrix.all_required_checks_passed:
            raise ValueError("candidate compatibility matrix failed")
        return matrix

    def validate_migration_manifest(
        self, manifest: V02CandidateMigrationManifest
    ) -> V02CandidateMigrationManifest:
        if manifest.candidate_delta_migrations_added or manifest.production_migration_executed:
            raise ValueError("AION-243 must not add or execute production migrations")
        return manifest

    def validate_release_notes(
        self, record: V02CandidateReleaseNotesRecord
    ) -> V02CandidateReleaseNotesRecord:
        if not record.draft or record.v02_released:
            raise ValueError("candidate release notes must remain draft-only")
        return record

    def validate_retention(
        self, result: V02CandidateRetentionResult
    ) -> V02CandidateRetentionResult:
        if not result.candidate_bundle_retained or result.candidate_bundle_count != 1:
            raise ValueError("exactly one local candidate bundle must be retained")
        if not result.candidate_local_image_retained or result.candidate_local_image_count != 1:
            raise ValueError("exactly one local candidate image must be retained")
        if (
            result.temporary_build_directories_retained
            or result.comparison_images_retained
            or result.private_qualification_keys_retained
        ):
            raise ValueError("temporary resources and private keys must not be retained")
        return result

    def audit_integrity(
        self, report: V02CandidateIntegrityReport
    ) -> V02CandidateIntegrityReport:
        if not report.integrity_passed or report.unknown_files:
            raise ValueError("candidate integrity report failed")
        return report

    def create_evidence_bundle(
        self, evidence: V02CandidateEvidenceBundle
    ) -> V02CandidateEvidenceBundle:
        if not evidence.integrity.integrity_passed:
            raise ValueError("cannot store failed candidate evidence")
        request_fingerprint = evidence.evidence_bundle_fingerprint
        return self.repository.store_evidence(evidence, request_fingerprint)

    def replay_exact_candidate(
        self, candidate_label: str, request_fingerprint: str
    ) -> V02CandidateEvidenceBundle:
        if self.repository.request_fingerprint(candidate_label) != request_fingerprint:
            raise ValueError("candidate replay fingerprint mismatch")
        return self.repository.evidence(candidate_label)

    def reject_changed_replay(self, candidate_label: str) -> bool:
        try:
            self.replay_exact_candidate(candidate_label, "changed")
        except ValueError:
            return True
        return False

    def close_session(self, session_id: str) -> V02ReleaseCandidateSession:
        return self.repository.close_session(session_id)
