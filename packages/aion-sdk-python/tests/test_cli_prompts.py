from __future__ import annotations

import json
from typing import Any

from typer.testing import CliRunner

from aion_sdk.cli import main as cli_main
from aion_sdk.config import AIONClientConfig

runner = CliRunner()


class FakePrompts:
    def compile(self, payload: dict[str, Any]) -> dict[str, object]:
        return {"compiled": True, "payload": payload}

    def preview(self, payload: dict[str, Any]) -> dict[str, object]:
        return {"preview": True, "payload": payload}

    def list_packets(self, scope: list[str], **kwargs: object) -> dict[str, object]:
        return {"packets": [], "scope": scope, "kwargs": kwargs}

    def seed_templates(self, scope: list[str], *, dry_run: bool = True) -> dict[str, object]:
        return {"dry_run": dry_run, "scope": scope}

    def list_templates(self, scope: list[str], **kwargs: object) -> dict[str, object]:
        return {"templates": [], "scope": scope, "kwargs": kwargs}

    def list_fragments(self, scope: list[str], **kwargs: object) -> dict[str, object]:
        return {"fragments": [], "scope": scope, "kwargs": kwargs}

    def boundary_check(self, prompt_packet_id: str, scope: list[str]) -> dict[str, object]:
        return {"boundary_check": prompt_packet_id, "scope": scope}

    def injection_findings(self, **kwargs: object) -> dict[str, object]:
        return {"injections": [], "kwargs": kwargs}

    def list_manifests(self, scope: list[str], **kwargs: object) -> dict[str, object]:
        return {"manifests": [], "scope": scope, "kwargs": kwargs}


class FakeClient:
    def __init__(self, config: AIONClientConfig) -> None:
        self.config = config
        self.prompts = FakePrompts()


def test_cli_prompts_compile_and_preview(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setattr(cli_main, "make_client", lambda config: FakeClient(config))

    compiled = runner.invoke(
        cli_main.app,
        ["--json", "prompts", "compile", "--user-message", "answer"],
    )
    preview = runner.invoke(
        cli_main.app,
        ["--json", "prompts", "preview", "--prompt-packet-id", "packet-1"],
    )

    assert compiled.exit_code == 0
    assert json.loads(compiled.stdout)["compiled"] is True
    assert preview.exit_code == 0
    assert json.loads(preview.stdout)["preview"] is True


def test_cli_prompts_lists(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setattr(cli_main, "make_client", lambda config: FakeClient(config))

    packets = runner.invoke(cli_main.app, ["--json", "prompts", "packets"])
    templates = runner.invoke(cli_main.app, ["--json", "prompts", "templates", "list"])
    fragments = runner.invoke(cli_main.app, ["--json", "prompts", "fragments", "list"])
    seeded = runner.invoke(cli_main.app, ["--json", "prompts", "templates", "seed"])
    boundary = runner.invoke(
        cli_main.app,
        ["--json", "prompts", "boundary-check", "--prompt-packet-id", "packet-1"],
    )
    injections = runner.invoke(cli_main.app, ["--json", "prompts", "injection-findings"])
    manifests = runner.invoke(cli_main.app, ["--json", "prompts", "manifests"])

    assert packets.exit_code == 0
    assert templates.exit_code == 0
    assert fragments.exit_code == 0
    assert seeded.exit_code == 0
    assert boundary.exit_code == 0
    assert injections.exit_code == 0
    assert manifests.exit_code == 0
