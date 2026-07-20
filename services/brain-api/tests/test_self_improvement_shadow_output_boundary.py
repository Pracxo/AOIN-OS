"""AION-178 shadow output-boundary tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from test_self_improvement_shadow_contracts import ROOT, make_manifest, make_pipeline

from aion_brain.self_improvement.shadow_budget import ShadowResourceBudget
from aion_brain.self_improvement.shadow_runner import ControlledShadowModeRunner


def test_no_output_is_written_by_default(tmp_path: Path) -> None:
    runner = ControlledShadowModeRunner(pipeline=make_pipeline())
    result = runner.run(make_manifest())

    assert result.written is False
    assert result.output_files == ()
    assert list(tmp_path.iterdir()) == []


def test_absolute_existing_temp_directory_is_accepted(tmp_path: Path) -> None:
    runner = ControlledShadowModeRunner(
        pipeline=make_pipeline(),
        repository_root=ROOT,
    )

    result = runner.run(make_manifest(), output_directory=tmp_path)

    assert result.written is True
    assert result.output_files == ("shadow-run-1.json",)
    output = tmp_path / result.output_files[0]
    assert not output.name.startswith(".")
    assert json.loads(output.read_text(encoding="utf-8"))["run_id"] == "shadow-run-1"


@pytest.mark.parametrize("path_factory", (Path, lambda _: ROOT, lambda _: ROOT / "docs"))
def test_relative_repository_and_descendant_paths_are_rejected(path_factory: object) -> None:
    runner = ControlledShadowModeRunner(pipeline=make_pipeline(), repository_root=ROOT)
    path = path_factory("relative-output") if callable(path_factory) else Path("relative-output")

    with pytest.raises(RuntimeError, match="shadow_output_boundary_rejected"):
        runner.run(make_manifest(), output_directory=path)


def test_hidden_directory_symlink_overwrite_and_size_limits_are_rejected(tmp_path: Path) -> None:
    runner = ControlledShadowModeRunner(pipeline=make_pipeline(), repository_root=ROOT)
    hidden = tmp_path / ".shadow"
    hidden.mkdir()
    with pytest.raises(RuntimeError, match="shadow_output_boundary_rejected"):
        runner.run(make_manifest(), output_directory=hidden)

    symlink = tmp_path / "link"
    symlink.symlink_to(ROOT)
    with pytest.raises(RuntimeError, match="shadow_output_boundary_rejected"):
        runner.run(make_manifest(), output_directory=symlink)

    (tmp_path / "shadow-run-1.json").write_text("{}", encoding="utf-8")
    with pytest.raises(RuntimeError, match="shadow_output_boundary_rejected"):
        runner.run(make_manifest(), output_directory=tmp_path)

    small_budget_runner = ControlledShadowModeRunner(
        pipeline=make_pipeline(budget=ShadowResourceBudget(maximum_output_bytes=2)),
        repository_root=ROOT,
    )
    fresh = tmp_path / "fresh"
    fresh.mkdir()
    with pytest.raises(RuntimeError, match="shadow_output_boundary_rejected"):
        small_budget_runner.run(make_manifest(), output_directory=fresh)
