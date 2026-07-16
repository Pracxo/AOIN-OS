"""AION-154 Phase 0 CI regression closure tests."""

from __future__ import annotations

import os
import shlex
import stat
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PYTHON_HELPER = ROOT / "scripts/lib/python-selection.sh"
TAG_HELPER = ROOT / "scripts/lib/immutable-tags.sh"
EXPECTED_AION_V01_SHA = "105fe29348160a2218ac095cfffadcb6f234421f"


def test_aion_brain_python_override_is_honored(tmp_path: Path) -> None:
    fake_python = _write_executable(tmp_path / "custom-python")

    result = _run_python_helper(
        "aion_select_brain_python " + shlex.quote(str(tmp_path)),
        cwd=tmp_path,
        env={"AION_BRAIN_PYTHON": str(fake_python), "PATH": ""},
    )

    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == str(fake_python)


def test_repository_venv_is_selected_when_available(tmp_path: Path) -> None:
    venv_python = _write_executable(tmp_path / "services/brain-api/.venv/bin/python")
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    _write_executable(fake_bin / "python3")

    result = _run_python_helper(
        "aion_select_brain_python " + shlex.quote(str(tmp_path)),
        cwd=tmp_path,
        env={"PATH": str(fake_bin)},
    )

    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == str(venv_python)


def test_python3_is_selected_when_repository_venv_is_absent(tmp_path: Path) -> None:
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    python3 = _write_executable(fake_bin / "python3")

    result = _run_python_helper(
        "aion_select_brain_python " + shlex.quote(str(tmp_path)),
        cwd=tmp_path,
        env={"PATH": str(fake_bin)},
    )

    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == str(python3)


def test_python_is_used_only_when_python3_is_unavailable(tmp_path: Path) -> None:
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    python = _write_executable(fake_bin / "python")

    result = _run_python_helper(
        "aion_select_brain_python " + shlex.quote(str(tmp_path)),
        cwd=tmp_path,
        env={"PATH": str(fake_bin)},
    )

    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == str(python)


def test_missing_interpreter_fails_with_clear_error(tmp_path: Path) -> None:
    empty_bin = tmp_path / "empty-bin"
    empty_bin.mkdir()

    result = _run_python_helper(
        "aion_select_brain_python " + shlex.quote(str(tmp_path)),
        cwd=tmp_path,
        env={"PATH": str(empty_bin)},
    )

    assert result.returncode != 0
    assert "No Python interpreter found" in result.stderr


def test_selected_interpreter_imports_required_test_dependencies() -> None:
    result = _run_python_helper(
        "aion_verify_brain_python_test_dependencies " + shlex.quote(sys.executable),
        cwd=ROOT,
    )

    assert result.returncode == 0, result.stderr


def test_dependency_verification_fails_for_incomplete_interpreter(tmp_path: Path) -> None:
    fake_python = _write_executable(tmp_path / "python", "#!/usr/bin/env sh\nexit 1\n")

    result = _run_python_helper(
        "aion_verify_brain_python_test_dependencies " + shlex.quote(str(fake_python)),
        cwd=tmp_path,
    )

    assert result.returncode != 0
    assert "pytest, pydantic" in result.stderr


def test_production_auth_gate_uses_shared_python_selector() -> None:
    script = (ROOT / "scripts/production-auth-core-check.sh").read_text(encoding="utf-8")

    assert "scripts/lib/python-selection.sh" in script
    assert "python_bin()" not in script
    assert "aion_select_brain_python" in script
    assert "aion_verify_brain_python_test_dependencies" in script


def test_missing_local_aion_v01_tag_is_recovered_by_exact_fetch(tmp_path: Path) -> None:
    _ensure_root_aion_v01_tag_available()
    repo = _init_temp_repo(tmp_path / "repo")
    _git(repo, "remote", "add", "origin", str(ROOT))

    result = _run_tag_helper("aion_ensure_immutable_v01_tag", cwd=repo)

    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == EXPECTED_AION_V01_SHA
    assert _git(repo, "rev-list", "-n", "1", "aion-v0.1.0").stdout.strip() == (
        EXPECTED_AION_V01_SHA
    )


def test_aion_v01_tag_sha_mismatch_fails_closed(tmp_path: Path) -> None:
    repo = _init_temp_repo(tmp_path / "repo")
    _git(repo, "tag", "aion-v0.1.0")
    _git(repo, "remote", "add", "origin", str(ROOT))

    result = _run_tag_helper("aion_ensure_immutable_v01_tag", cwd=repo)

    assert result.returncode != 0
    assert "must remain at" in result.stderr


def test_detached_checkout_tag_confirmation_is_nonfatal(tmp_path: Path) -> None:
    _ensure_root_aion_v01_tag_available()
    repo = _init_temp_repo(tmp_path / "repo")
    _git(repo, "remote", "add", "origin", str(ROOT))
    _git(repo, "checkout", "--detach", "HEAD")

    result = _run_tag_helper("aion_confirm_immutable_v01_tag_history", cwd=repo)

    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == EXPECTED_AION_V01_SHA


def test_aion_v01_tag_gates_use_shared_immutable_tag_helper() -> None:
    for path in sorted((ROOT / "scripts").glob("*.sh")):
        text = path.read_text(encoding="utf-8")
        assert "if git_ref_exists aion-v0.1.0" not in text, path
        assert "git rev-parse aion-v0.1.0" not in text, path
        assert "git merge-base --is-ancestor aion-v0.1.0" not in text, path
        if "aion_confirm_immutable_v01_tag_history" in text:
            assert "scripts/lib/immutable-tags.sh" in text, path


def test_validation_script_self_edits_do_not_false_positive() -> None:
    result = subprocess.run(
        [str(ROOT / "scripts/production-auth-core-no-go-regression.sh")],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr


def test_unauthorized_production_auth_source_changes_still_fail() -> None:
    target = ROOT / "services/brain-api/src/aion_brain/production_auth/phase0_forbidden.py"
    target.write_text("FORBIDDEN = True\n", encoding="utf-8")
    try:
        result = subprocess.run(
            [str(ROOT / "scripts/production-auth-core-no-go-regression.sh")],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
    finally:
        target.unlink(missing_ok=True)

    assert result.returncode != 0
    assert "production-auth source, config, or kernel changes are forbidden" in result.stderr


def test_unauthorized_runtime_surfaces_still_fail() -> None:
    target = ROOT / "docs/platform/aion154-runtime-violation.md"
    target.write_text(
        "production_auth_runtime_enabled" + ": " + "true\n",
        encoding="utf-8",
    )
    try:
        result = subprocess.run(
            [str(ROOT / "scripts/production-auth-core-no-go-regression.sh")],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
    finally:
        target.unlink(missing_ok=True)

    assert result.returncode != 0
    assert "runtime, route, storage, provider" in result.stderr


def test_scanner_exclusions_do_not_use_broad_directories() -> None:
    text = (ROOT / "scripts/lib/v02-production-auth-scan-exclusions.sh").read_text(
        encoding="utf-8"
    )
    no_go = (ROOT / "scripts/production-auth-core-no-go-regression.sh").read_text(
        encoding="utf-8"
    )

    for forbidden in [
        "scripts/*",
        "services/*",
        "services/brain-api/src/*",
        "services/brain-api/src/aion_brain/production_auth/*",
    ]:
        assert forbidden not in text

    for forbidden in [
        "scripts/*",
        "services/*",
        "services/brain-api/src/*",
    ]:
        assert forbidden not in no_go

    assert "scripts/production-auth-core-check.sh" in no_go
    assert "scripts/production-auth-core-no-go-regression.sh" in no_go


def _run_python_helper(
    command: str,
    *,
    cwd: Path,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    shell = "source " + shlex.quote(str(PYTHON_HELPER)) + "\n" + command
    merged_env = os.environ.copy()
    if env is not None:
        merged_env.update(env)
    return subprocess.run(
        ["/bin/bash", "-c", shell],
        cwd=cwd,
        env=merged_env,
        capture_output=True,
        text=True,
        check=False,
    )


def _run_tag_helper(command: str, *, cwd: Path) -> subprocess.CompletedProcess[str]:
    shell = "source " + shlex.quote(str(TAG_HELPER)) + "\n" + command
    return subprocess.run(
        ["/bin/bash", "-c", shell],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
    )


def _init_temp_repo(path: Path) -> Path:
    path.mkdir()
    subprocess.run(["git", "init"], cwd=path, check=True, capture_output=True, text=True)
    _git(path, "checkout", "-b", "main")
    _git(path, "config", "user.email", "aion@example.test")
    _git(path, "config", "user.name", "AION Test")
    (path / "README.md").write_text("temp repo\n", encoding="utf-8")
    _git(path, "add", "README.md")
    _git(path, "commit", "-m", "init")
    return path


def _ensure_root_aion_v01_tag_available() -> None:
    exists = subprocess.run(
        ["git", "rev-parse", "--verify", "--quiet", "aion-v0.1.0^{commit}"],
        cwd=ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    if exists.returncode != 0:
        subprocess.run(
            [
                "git",
                "fetch",
                "--no-tags",
                "origin",
                "refs/tags/aion-v0.1.0:refs/tags/aion-v0.1.0",
            ],
            cwd=ROOT,
            check=True,
        )
    tag_ref = _git(ROOT, "rev-list", "-n", "1", "aion-v0.1.0").stdout.strip()
    assert tag_ref == EXPECTED_AION_V01_SHA


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=repo,
        capture_output=True,
        text=True,
        check=True,
    )


def _write_executable(path: Path, content: str = "#!/usr/bin/env sh\nexit 0\n") -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    path.chmod(path.stat().st_mode | stat.S_IXUSR)
    return path
