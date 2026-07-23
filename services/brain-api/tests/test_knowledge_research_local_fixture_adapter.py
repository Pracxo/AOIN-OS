from __future__ import annotations

import json

import pytest
from test_knowledge_research_fetch_adapters import valid_request

from aion_brain.knowledge_intelligence.research_adapters import ExplicitLocalFixtureResearchAdapter


def test_local_fixture_adapter_accepts_exact_synthetic_envelope(tmp_path):
    fixture = tmp_path / "fixture.json"
    fixture.write_text(
        json.dumps(
            {
                "synthetic": True,
                "redacted": True,
                "request_method": "GET",
                "canonical_url": "https://research.example.invalid/source.txt",
                "status_code": 200,
                "peer_address": "93.184.216.34",
                "response_headers": {"Content-Type": "text/plain"},
                "content_type": "text/plain",
                "character_encoding": "utf-8",
                "body_utf8": "synthetic fixture body",
            }
        ),
        encoding="utf-8",
    )
    response = ExplicitLocalFixtureResearchAdapter(
        fixture,
        repository_root=tmp_path / "repo",
    ).fetch(valid_request())
    assert response.body == b"synthetic fixture body"


def test_local_fixture_adapter_rejects_missing_repo_hidden_symlink_and_protected(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    with pytest.raises(ValueError):
        ExplicitLocalFixtureResearchAdapter(repo / "fixture.json", repository_root=repo)
    repo_fixture = repo / "fixture.json"
    repo_fixture.write_text("{}", encoding="utf-8")
    with pytest.raises(ValueError):
        ExplicitLocalFixtureResearchAdapter(repo_fixture, repository_root=repo)
    hidden = tmp_path / ".fixture.json"
    hidden.write_text("{}", encoding="utf-8")
    with pytest.raises(ValueError):
        ExplicitLocalFixtureResearchAdapter(hidden, repository_root=repo)
    visible = tmp_path / "visible.json"
    visible.write_text("{}", encoding="utf-8")
    visible_link = tmp_path / "visible-link.json"
    visible_link.symlink_to(visible)
    with pytest.raises(ValueError):
        ExplicitLocalFixtureResearchAdapter(visible_link, repository_root=repo)
    link = tmp_path / "link.json"
    link.symlink_to(hidden)
    with pytest.raises(ValueError):
        ExplicitLocalFixtureResearchAdapter(link, repository_root=repo)
