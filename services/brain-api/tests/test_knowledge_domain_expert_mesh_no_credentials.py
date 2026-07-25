from aion_brain.contracts.knowledge_domain_expert_mesh import validate_mesh_text


def test_credentials_and_tokens_are_rejected_from_safe_text():
    try:
        validate_mesh_text("bearer secret value", "mesh text")
    except ValueError:
        return
    raise AssertionError("credential marker must be rejected")
