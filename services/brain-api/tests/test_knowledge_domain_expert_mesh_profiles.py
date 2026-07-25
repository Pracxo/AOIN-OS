from aion_brain.contracts.knowledge_domain_expert_mesh import ExpertPerspectiveRole
from aion_brain.knowledge_intelligence.domain_expert_profiles import (
    build_default_domain_taxonomy,
    build_default_profile_registry,
)


def test_default_profiles_are_computational_and_cover_roles():
    registry = build_default_profile_registry(build_default_domain_taxonomy())
    roles = {role for profile in registry.profiles for role in profile.perspective_roles}
    assert ExpertPerspectiveRole.DOMAIN_ANALYST in roles
    assert ExpertPerspectiveRole.EVIDENCE_AUDITOR in roles
    assert ExpertPerspectiveRole.METHODOLOGICAL_SKEPTIC in roles
    assert all(profile.computational_profile for profile in registry.profiles)
    assert not any(profile.human_identity_claimed for profile in registry.profiles)
