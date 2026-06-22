"""Langfuse placeholder boundary tests."""

import pytest

from aion_brain.observability.langfuse_adapter import LangfuseAdapter
from tests.test_observability_contracts import event


def test_langfuse_adapter_is_placeholder_without_sdk() -> None:
    """The future adapter remains a non-executable boundary."""
    adapter = LangfuseAdapter()
    assert "AION contracts must remain independent" in (LangfuseAdapter.__doc__ or "")
    with pytest.raises(NotImplementedError):
        adapter.record_event(event())
    with pytest.raises(NotImplementedError):
        adapter.summarize(["workspace:main"])
