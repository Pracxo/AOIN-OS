from __future__ import annotations

from typing import Any

import httpx

from aion_sdk import AIONClient, AIONClientConfig


def _client(handler: Any) -> AIONClient:
    return AIONClient(
        AIONClientConfig(base_url="http://aion.test"),
        httpx.Client(transport=httpx.MockTransport(handler)),
    )


def test_release_candidate_resource_calls_create_and_run_endpoints() -> None:
    seen: list[tuple[str, str]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append((request.method, request.url.path))
        return httpx.Response(200, json={"status": "ok"})

    client = _client(handler)
    client.release_candidate.create_candidate({"rc_key": "rc.test", "version": "0.1.0"})
    client.release_candidate.run_gate({"owner_scope": ["workspace:main"]})

    assert seen == [
        ("POST", "/brain/rc/candidates"),
        ("POST", "/brain/rc/gate/run"),
    ]


def test_release_candidate_resource_calls_matrix_and_report_endpoints() -> None:
    seen: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request.url.path)
        return httpx.Response(200, json=[])

    client = _client(handler)
    client.release_candidate.list_matrices(["workspace:main"])
    client.release_candidate.seed_default_matrices(["workspace:main"])
    client.release_candidate.list_reports(["workspace:main"])
    client.release_candidate.get_report("report-1", ["workspace:main"])

    assert seen == [
        "/brain/rc/matrices",
        "/brain/rc/matrices/seed-defaults",
        "/brain/rc/reports",
        "/brain/rc/reports/report-1",
    ]


def test_release_candidate_resource_calls_findings_evidence_and_query_endpoints() -> None:
    seen: list[tuple[str, str]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append((request.method, request.url.path))
        return httpx.Response(200, json={})

    client = _client(handler)
    client.release_candidate.list_findings(["workspace:main"], blocking=True)
    client.release_candidate.dismiss_finding("finding-1", ["workspace:main"], reason="reviewed")
    client.release_candidate.list_evidence_packs(["workspace:main"])
    client.release_candidate.get_evidence_pack("pack-1", ["workspace:main"])
    client.release_candidate.query({"scope": ["workspace:main"]})

    assert seen == [
        ("GET", "/brain/rc/findings"),
        ("POST", "/brain/rc/findings/finding-1/dismiss"),
        ("GET", "/brain/rc/evidence-packs"),
        ("GET", "/brain/rc/evidence-packs/pack-1"),
        ("POST", "/brain/rc/query"),
    ]
