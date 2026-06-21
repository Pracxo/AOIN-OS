from __future__ import annotations

from typing import Any

import httpx

from aion_sdk import AIONClient, AIONClientConfig


def _client(handler: Any) -> AIONClient:
    return AIONClient(
        AIONClientConfig(base_url="http://aion.test"),
        httpx.Client(transport=httpx.MockTransport(handler)),
    )


def test_lifecycle_resource_calls_expected_endpoints() -> None:
    seen: list[tuple[str, str]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append((request.method, request.url.path))
        return httpx.Response(200, json={"ok": True})

    client = _client(handler)
    client.lifecycle.create_policy({"name": "policy"})
    client.lifecycle.seed_default_policies(["workspace:main"])
    client.lifecycle.list_policies(["workspace:main"])
    client.lifecycle.get_policy("policy-1", ["workspace:main"])
    client.lifecycle.evaluate({"owner_scope": ["workspace:main"]})
    client.lifecycle.get_evaluation("eval-1", ["workspace:main"])
    client.lifecycle.list_classifications(["workspace:main"])
    client.lifecycle.list_archive_candidates(["workspace:main"])
    client.lifecycle.dismiss_archive_candidate("archive-1", "dismiss")
    client.lifecycle.convert_archive_candidate("archive-1", "convert")
    client.lifecycle.list_redaction_candidates(["workspace:main"])
    client.lifecycle.dismiss_redaction_candidate("redaction-1", "dismiss")
    client.lifecycle.convert_redaction_candidate("redaction-1", "convert")
    client.lifecycle.create_purge_preview(["aion://generic/res-1"], ["workspace:main"])
    client.lifecycle.list_purge_previews(["workspace:main"])
    client.lifecycle.review_candidate({"candidate_type": "archive", "candidate_id": "archive-1"})
    client.lifecycle.list_reviews(["workspace:main"])
    client.lifecycle.report(["workspace:main"])

    assert seen == [
        ("POST", "/brain/lifecycle/policies"),
        ("POST", "/brain/lifecycle/policies/seed-defaults"),
        ("GET", "/brain/lifecycle/policies"),
        ("GET", "/brain/lifecycle/policies/policy-1"),
        ("POST", "/brain/lifecycle/evaluate"),
        ("GET", "/brain/lifecycle/evaluations/eval-1"),
        ("GET", "/brain/lifecycle/classifications"),
        ("GET", "/brain/lifecycle/archive-candidates"),
        ("POST", "/brain/lifecycle/archive-candidates/archive-1/dismiss"),
        ("POST", "/brain/lifecycle/archive-candidates/archive-1/convert-to-action-proposal"),
        ("GET", "/brain/lifecycle/redaction-candidates"),
        ("POST", "/brain/lifecycle/redaction-candidates/redaction-1/dismiss"),
        ("POST", "/brain/lifecycle/redaction-candidates/redaction-1/convert-to-action-proposal"),
        ("POST", "/brain/lifecycle/purge-preview"),
        ("GET", "/brain/lifecycle/purge-previews"),
        ("POST", "/brain/lifecycle/reviews"),
        ("GET", "/brain/lifecycle/reviews"),
        ("POST", "/brain/lifecycle/report"),
    ]


def test_lifecycle_resource_does_not_import_brain_package() -> None:
    import aion_sdk.resources.lifecycle as resource

    assert "aion_brain" not in resource.__dict__
