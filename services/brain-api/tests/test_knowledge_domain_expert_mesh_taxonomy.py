from aion_brain.knowledge_intelligence.domain_expert_profiles import (
    TOP_LEVEL_DOMAIN_IDS,
    build_default_domain_taxonomy,
)


def test_default_taxonomy_has_required_explicit_domains():
    taxonomy = build_default_domain_taxonomy()
    assert set(TOP_LEVEL_DOMAIN_IDS).issubset(taxonomy.top_level_domain_ids)
    assert len(taxonomy.top_level_domain_ids) == 18
    assert taxonomy.dynamic_domain_creation_enabled is False
    assert taxonomy.embedding_classification_enabled is False
    assert taxonomy.universal_wildcard_domain_enabled is False
