from knowledge_domain_expert_mesh_test_helpers import make_case
from pydantic import ValidationError

from aion_brain.contracts.knowledge_domain_expert_mesh import DomainExpertCase


def test_case_requires_explicit_domain_tags_and_redaction():
    case = make_case()
    assert case.operator_supplied is True
    assert case.read_only is True
    assert case.redacted is True
    payload = case.model_dump()
    payload["domain_ids"] = ()
    payload["case_fingerprint"] = "0" * 64
    try:
        DomainExpertCase.model_validate(payload)
    except ValidationError:
        return
    raise AssertionError("empty domains must be rejected")
