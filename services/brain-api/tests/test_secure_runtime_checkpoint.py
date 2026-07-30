from __future__ import annotations

from tests.secure_runtime_test_support import secure_runtime_fixture


def test_checkpoint_is_temporary_and_redacted() -> None:
    fixture = secure_runtime_fixture()

    assert fixture.checkpoint.temporary is True
    assert fixture.checkpoint.persistent_session is False
    assert fixture.checkpoint.production_effect is False
    assert fixture.checkpoint.checkpoint_fingerprint
