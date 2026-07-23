from __future__ import annotations

from pathlib import Path

HARNESS = Path(__file__).resolve().parents[3] / (
    "scripts/lib/knowledge_intelligence_research_operator_evaluation.py"
)


def test_operator_evaluation_harness_has_no_network_git_or_provider_imports():
    text = HARNESS.read_text()
    prohibited = (
        "import socket",
        "import requests",
        "import httpx",
        "import aiohttp",
        "import urllib.request",
        "import subprocess",
        "import git",
        "import github",
        "browser automation",
        "connector clients",
        "model providers",
        "cognitive belief services",
        "verified knowledge services",
    )
    for marker in prohibited:
        assert marker not in text


def test_operator_evaluation_harness_writes_only_to_explicit_report_path():
    text = HARNESS.read_text()
    assert ".git" not in text
    assert "args.report.write_text" in text
    assert "repo_root.write_text" not in text
