from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def test_no_runtime_routes_or_private_key_runtime_source() -> None:
    forbidden_routes = [
        ROOT / "services/brain-api/src/aion_brain/api/identity_assertion.py",
        ROOT / "services/brain-api/src/aion_brain/api/production_auth.py",
        ROOT / "services/brain-api/src/aion_brain/api/request_identity.py",
        ROOT / "services/brain-api/src/aion_brain/api/actor_context.py",
    ]
    assert all(not path.exists() for path in forbidden_routes)
    runtime_source = ROOT / "services/brain-api/src/aion_brain"
    forbidden = (
        "Ed25519PrivateKey",
        "private_" "bytes(",
        "load_pem_private_key",
        "BEGIN " "PRIVATE KEY",
        "BEGIN " "OPENSSH PRIVATE KEY",
        "signing_" "key",
        "private_" "key_seed",
        "private_" "key_base64",
    )
    for path in runtime_source.rglob("*.py"):
        text = path.read_text()
        for marker in forbidden:
            assert marker not in text, f"{marker} found in {path}"


def test_no_sdk_migrations_or_lockfiles_added() -> None:
    assert not (ROOT / "services/brain-api/src/aion_brain/api/identity_assertion.py").exists()
    identity_migrations = (
        list((ROOT / "migrations").glob("*identity*")) if (ROOT / "migrations").exists() else []
    )
    assert not identity_migrations
    assert not (ROOT / "package-lock.json").exists()
