"""Connector contract tests."""

import pytest
from pydantic import ValidationError

from tests.sandbox_fakes import connector_request


def test_connector_definition_validates_connector_type() -> None:
    with pytest.raises(ValidationError):
        connector_request(connector_type="live_connector")


def test_connector_definition_rejects_domain_specific_actions() -> None:
    with pytest.raises(ValidationError):
        connector_request(allowed_actions=["finance.read"])
