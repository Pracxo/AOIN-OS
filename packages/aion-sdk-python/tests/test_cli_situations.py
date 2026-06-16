from __future__ import annotations

from typer.testing import CliRunner

from aion_sdk.cli.main import app


def test_cli_situations_group_is_registered() -> None:
    result = CliRunner().invoke(app, ["situations", "--help"])

    assert result.exit_code == 0
    assert "Situation model commands" in result.stdout
