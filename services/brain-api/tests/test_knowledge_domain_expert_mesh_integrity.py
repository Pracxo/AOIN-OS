from knowledge_domain_expert_mesh_test_helpers import MESH_TEST_NOW, run_sample_session

from aion_brain.contracts.knowledge_domain_expert_mesh import MeshIntegrityStatus
from aion_brain.knowledge_intelligence.domain_expert_integrity import (
    audit_domain_expert_mesh_session,
)


def test_integrity_audit_passes_safe_session():
    _, _, _, session = run_sample_session()
    report = audit_domain_expert_mesh_session(session, clock=lambda: MESH_TEST_NOW)
    assert report.status == MeshIntegrityStatus.PASSED
    assert report.finding_count == 0
