import json

from knowledge_domain_expert_mesh_test_helpers import MESH_TEST_NOW, make_assessment, make_case

from aion_brain.contracts.knowledge_domain_expert_mesh import DomainExpertMeshFixtureEnvelope
from aion_brain.knowledge_intelligence.domain_expert_mesh import (
    ControlledDomainExpertMesh,
    domain_expert_mesh_fixture_payload,
)


def test_fixture_replay_accepts_only_explicit_local_file(tmp_path):
    case = make_case()
    assessment = make_assessment()
    payload = domain_expert_mesh_fixture_payload(case=case, assessments=(assessment,))
    envelope = DomainExpertMeshFixtureEnvelope.model_validate(payload)
    fixture_path = tmp_path / "domain-mesh-fixture.json"
    fixture_path.write_text(json.dumps(envelope.model_dump(mode="json")), encoding="utf-8")
    mesh = ControlledDomainExpertMesh(
        clock=lambda: MESH_TEST_NOW, repository_root=tmp_path / "repo"
    )
    session = mesh.replay_fixture(fixture_path)
    assert session.case.case_id == case.case_id
    assert session.persistent_write_applied is False
