from knowledge_intelligence_test_helpers import read_json, read_text


def test_research_boundary_documents_transport_and_destination_rules():
    text = read_text("docs/knowledge-intelligence/security-boundary.md")
    for term in (
        "only HTTPS by default",
        "explicit domain allowlist",
        "no private address space",
        "no loopback",
        "no link-local",
        "no multicast",
        "DNS resolution before request",
        "redirect destination revalidation",
        "TLS certificate validation",
        "bounded response streaming",
        "no cookies",
        "no authorization headers",
        "no HTML script execution",
        "no browser storage",
    ):
        assert term in text


def test_plan_boundary_allows_get_head_only_and_blocks_writes():
    payload = read_json("examples/knowledge-intelligence/research-plan-boundary.json")
    assert payload["allowed_methods"] == ["GET", "HEAD"]
    for method in ["POST", "PUT", "PATCH", "DELETE"]:
        assert method in payload["prohibited_methods"]
    for key in (
        "domain_allowlist_required",
        "private_and_local_destinations_prohibited",
        "redirect_revalidation_required",
    ):
        assert payload[key] is True
    for key in (
        "javascript_execution_enabled",
        "browser_automation_enabled",
        "login_flow_enabled",
        "cookies_enabled",
        "credential_use_enabled",
        "content_promotion_enabled",
        "belief_mutation_enabled",
        "background_crawler_enabled",
    ):
        assert payload[key] is False
