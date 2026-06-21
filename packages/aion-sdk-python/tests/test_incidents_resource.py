from __future__ import annotations

from typing import Any

import httpx

from aion_sdk import AIONClient, AIONClientConfig


def _client(handler: Any) -> AIONClient:
    return AIONClient(
        AIONClientConfig(base_url="http://aion.test"),
        httpx.Client(transport=httpx.MockTransport(handler)),
    )


def test_incidents_resource_calls_expected_endpoints() -> None:
    seen: list[tuple[str, str]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append((request.method, request.url.path))
        return httpx.Response(200, json={"ok": True})

    client = _client(handler)
    client.incidents.create_signal({"source_id": "source-1"})
    client.incidents.list_signals(["workspace:main"])
    client.incidents.dismiss_signal("signal-1", "dismissed")
    client.incidents.create_incident({"incident_id": "incident-1"})
    client.incidents.get_incident("incident-1", ["workspace:main"])
    client.incidents.query({"scope": ["workspace:main"]})
    client.incidents.acknowledge("incident-1", "reviewed")
    client.incidents.resolve("incident-1", "resolved")
    client.incidents.dismiss("incident-1", "dismissed")
    client.incidents.archive("incident-1", "archived")
    client.incidents.create_rule({"correlation_rule_id": "rule-1"})
    client.incidents.list_rules(["workspace:main"])
    client.incidents.seed_rules(["workspace:main"])
    client.incidents.correlate({"owner_scope": ["workspace:main"]})
    client.incidents.get_correlation_run("run-1")
    client.incidents.generate_root_causes("incident-1", ["workspace:main"])
    client.incidents.create_root_cause({"incident_id": "incident-1"})
    client.incidents.list_root_causes("incident-1")
    client.incidents.confirm_root_cause("root-1", "confirmed")
    client.incidents.dismiss_root_cause("root-1", "dismissed")
    client.incidents.create_recovery_review({"incident_id": "incident-1"})
    client.incidents.get_recovery_review("review-1", ["workspace:main"])
    client.incidents.list_recovery_reviews(["workspace:main"])

    assert seen == [
        ("POST", "/brain/incidents/signals"),
        ("GET", "/brain/incidents/signals"),
        ("POST", "/brain/incidents/signals/signal-1/dismiss"),
        ("POST", "/brain/incidents"),
        ("GET", "/brain/incidents/incident-1"),
        ("POST", "/brain/incidents/query"),
        ("POST", "/brain/incidents/incident-1/acknowledge"),
        ("POST", "/brain/incidents/incident-1/resolve"),
        ("POST", "/brain/incidents/incident-1/dismiss"),
        ("POST", "/brain/incidents/incident-1/archive"),
        ("POST", "/brain/incidents/rules"),
        ("GET", "/brain/incidents/rules"),
        ("POST", "/brain/incidents/rules/seed-defaults"),
        ("POST", "/brain/incidents/correlate"),
        ("GET", "/brain/incidents/correlation-runs/run-1"),
        ("POST", "/brain/incidents/incident-1/root-cause-candidates/generate"),
        ("POST", "/brain/incidents/root-cause-candidates"),
        ("GET", "/brain/incidents/root-cause-candidates"),
        ("POST", "/brain/incidents/root-cause-candidates/root-1/confirm"),
        ("POST", "/brain/incidents/root-cause-candidates/root-1/dismiss"),
        ("POST", "/brain/incidents/recovery-reviews"),
        ("GET", "/brain/incidents/recovery-reviews/review-1"),
        ("GET", "/brain/incidents/recovery-reviews"),
    ]


def test_incidents_resource_does_not_import_brain_package() -> None:
    import aion_sdk.resources.incidents as resource

    assert "aion_brain" not in resource.__dict__
