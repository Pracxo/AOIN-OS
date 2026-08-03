#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
source "$ROOT_DIR/scripts/lib/python-selection.sh"
source "$ROOT_DIR/scripts/lib/portable-search.sh"

PYTHON_BIN="$(aion_select_brain_python "$ROOT_DIR")"
export AION_BRAIN_PYTHON="$PYTHON_BIN"

"$PYTHON_BIN" - <<'PY'
from __future__ import annotations

import json
import os
import shutil
import subprocess
import tomllib
from pathlib import Path

ROOT = Path.cwd()
EXPECTED_MAIN = "2a5db0760178698d783abcc63e53f08ff3583571"
EXPECTED_TAG = "aion-v0.2.0-rc.1"
EXPECTED_TARGET = "d35f1caa234d35dce1dfc0a80bc4c8e327a8373e"
EXPECTED_INVENTORY_FP = "c228cbe4d3a2ed993d329b1eeb03cddfbc6f6f0f18491bca54a6fd234c32dfcc"
REQUIRED_CHECKS = {
    "brain-api-quality",
    "contract-check",
    "docker-build-core",
    "policy-check",
    "repository-hygiene",
    "sdk-cli-check",
    "sdk-quality",
}


def run(args: list[str], *, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=ROOT, capture_output=True, text=True, check=check)


def gh_available() -> bool:
    if shutil.which("gh") is None:
        return False
    return run(["gh", "auth", "status"], check=False).returncode == 0


def gh_json(args: list[str]) -> object:
    return json.loads(run(["gh", *args]).stdout)


def version(path: str) -> str:
    with (ROOT / path).open("rb") as handle:
        return tomllib.load(handle)["project"]["version"]


if not run(["git", "merge-base", "--is-ancestor", EXPECTED_MAIN, "HEAD"], check=False).returncode == 0:
    raise SystemExit("AION-244 final main commit is not an ancestor of HEAD")

if run(["git", "cat-file", "-t", EXPECTED_TAG]).stdout.strip() != "tag":
    raise SystemExit("RC1 tag is not annotated")
if run(["git", "rev-parse", f"{EXPECTED_TAG}^{{}}"]).stdout.strip() != EXPECTED_TARGET:
    raise SystemExit("RC1 tag target mismatch")
remote_tag = run(["git", "ls-remote", "--tags", "origin", EXPECTED_TAG]).stdout.strip()
if EXPECTED_TAG not in remote_tag:
    raise SystemExit("RC1 remote tag is missing")

if run(["git", "tag", "--list", "aion-v0.2.0", "v0.2.0*"]).stdout.strip():
    raise SystemExit("stable v0.2 tag exists")

publication = json.loads(
    (ROOT / "examples/v02-release-qualification/v02-rc1-publication-evidence.json").read_text(encoding="utf-8")
)
for key, value in {
    "assets_uploaded": 24,
    "assets_downloaded_for_verification": 24,
    "asset_hash_matches": 24,
    "asset_hash_failures": 0,
    "created_tag_count": 1,
    "created_release_count": 1,
    "production_deployments": 0,
    "stable_tags_created": 0,
    "stable_releases_created": 0,
    "asset_inventory_fingerprint": EXPECTED_INVENTORY_FP,
}.items():
    if publication.get(key) != value:
        raise SystemExit(f"publication evidence mismatch {key}: {publication.get(key)!r}")

for relative in (
    "docs/v02-release-qualification/program-ledger.json",
    "docs/v02-release-qualification/authorization-ledger.json",
):
    payload = json.loads((ROOT / relative).read_text(encoding="utf-8"))
    if payload.get("v02_release_qualification_program_complete") is not True:
        raise SystemExit(f"{relative} programme is incomplete")
    if payload.get("active_v02_release_qualification_authorization_count") != 0:
        raise SystemExit(f"{relative} has active v0.2 authorization")

if version("services/brain-api/pyproject.toml") != "0.3.0.dev0":
    raise SystemExit("Brain API development version mismatch")
if version("packages/aion-sdk-python/pyproject.toml") != "0.3.0.dev0":
    raise SystemExit("SDK development version mismatch")

tagged_brain = run(
    ["git", "show", f"{EXPECTED_TAG}:services/brain-api/pyproject.toml"]
).stdout
tagged_sdk = run(
    ["git", "show", f"{EXPECTED_TAG}:packages/aion-sdk-python/pyproject.toml"]
).stdout
if 'version = "0.2.0rc1"' not in tagged_brain or 'version = "0.2.0rc1"' not in tagged_sdk:
    raise SystemExit("RC1 tagged source package version drifted")

if gh_available():
    for number, expected_head, expected_merge, expected_count in (
        (163, "6d5f16c266fd59815a64e3f743d321a3e4ff6cf0", "07d0cc4fe710066271d6e8ab2d03ad360be899bb", 2),
        (164, "7a6eb5e82e965787d333ca0144ed94173b6dc298", "2a5db0760178698d783abcc63e53f08ff3583571", 1),
    ):
        pr = gh_json([
            "pr",
            "view",
            str(number),
            "--json",
            "number,state,baseRefName,commits,mergeCommit",
        ])
        if pr["state"] != "MERGED" or pr["baseRefName"] != "main":
            raise SystemExit(f"PR #{number} is not merged into main")
        if pr["mergeCommit"]["oid"] != expected_merge:
            raise SystemExit(f"PR #{number} merge commit mismatch")
        commits = pr["commits"]
        if len(commits) != expected_count or commits[-1]["oid"] != expected_head:
            raise SystemExit(f"PR #{number} commit list mismatch")
        checks = gh_json(["pr", "checks", str(number), "--json", "name,state,bucket"])
        passed = {item["name"] for item in checks if item["state"] == "SUCCESS" and item["bucket"] == "pass"}
        missing = REQUIRED_CHECKS - passed
        if missing:
            raise SystemExit(f"PR #{number} missing passed checks: {sorted(missing)}")

    release = gh_json([
        "release",
        "view",
        EXPECTED_TAG,
        "--json",
        "tagName,name,isDraft,isPrerelease,publishedAt,assets,url,databaseId",
    ])
    if release["tagName"] != EXPECTED_TAG or release["name"] != "AION OS v0.2.0-rc.1":
        raise SystemExit("RC1 release identity mismatch")
    if release["isDraft"] is not False or release["isPrerelease"] is not True:
        raise SystemExit("RC1 release state mismatch")
    if len(release["assets"]) != 24:
        raise SystemExit("RC1 release asset count mismatch")
    if run(["gh", "release", "view", "aion-v0.2.0"], check=False).returncode == 0:
        raise SystemExit("stable aion-v0.2.0 release exists")
    if run(["gh", "release", "view", "v0.2.0"], check=False).returncode == 0:
        raise SystemExit("stable v0.2.0 release exists")

print("post-RC1 v0.3 development baseline PASS")
PY
