from secure_runtime_aion232_test_helpers import scenario


def test_request_identity_and_actor_context_do_not_expand_privilege() -> None:
    identity = scenario("secure_request_identity_origin")["requirements"]
    for key in (
        "actor_id_from_signed_assertion",
        "subject_from_signed_assertion",
        "workspace_from_signed_assertion",
        "roles_from_signed_assertion",
        "permissions_from_signed_assertion",
        "scopes_from_signed_assertion",
        "headers_cannot_supply_identity",
        "cookies_cannot_supply_identity",
        "tokens_cannot_supply_identity",
        "external_identity_providers_unused",
    ):
        assert identity[key] is True
    actor = scenario("actor_context_binding_and_no_privilege_expansion")["requirements"]
    for key in (
        "actor_context_exact",
        "actor_type_local_operator",
        "dev_mode_false",
        "anonymous_fallback_blocked",
        "role_escalation_rejected",
        "permission_escalation_rejected",
        "scope_escalation_rejected",
        "workspace_mismatch_rejected",
        "trace_and_correlation_preserved",
    ):
        assert actor[key] is True
