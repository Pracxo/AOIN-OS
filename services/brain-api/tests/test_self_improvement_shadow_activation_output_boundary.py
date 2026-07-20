"""AION-181 output-boundary tests."""

from __future__ import annotations

from pathlib import Path

from test_self_improvement_shadow_activation_contracts import NOW, make_context

from aion_brain.contracts.self_improvement_shadow_activation import (
    ShadowActivationOutputBoundary,
    validate_shadow_activation_output_boundary,
)


def test_output_boundary_accepts_explicit_existing_absolute_directory(tmp_path: Path) -> None:
    ctx = make_context(tmp_path)
    result = validate_shadow_activation_output_boundary(
        ctx["boundary"],
        repository_root=Path.cwd(),
    )
    assert result.valid is True


def test_output_boundary_rejects_repository_relative_hidden_and_symlink(tmp_path: Path) -> None:
    repository_boundary = ShadowActivationOutputBoundary(
        output_directory=str(Path.cwd()),
        created_at=NOW,
    )
    assert validate_shadow_activation_output_boundary(
        repository_boundary,
        repository_root=Path.cwd(),
    ).valid is False
    relative = ShadowActivationOutputBoundary(output_directory="relative", created_at=NOW)
    assert (
        validate_shadow_activation_output_boundary(relative, repository_root=Path.cwd()).valid
        is False
    )
    hidden_dir = tmp_path / ".hidden"
    hidden_dir.mkdir()
    hidden = ShadowActivationOutputBoundary(output_directory=str(hidden_dir), created_at=NOW)
    assert (
        validate_shadow_activation_output_boundary(hidden, repository_root=Path.cwd()).valid
        is False
    )
    real = tmp_path / "real"
    real.mkdir()
    link = tmp_path / "link"
    link.symlink_to(real)
    symlink = ShadowActivationOutputBoundary(output_directory=str(link), created_at=NOW)
    assert (
        validate_shadow_activation_output_boundary(symlink, repository_root=Path.cwd()).valid
        is False
    )
