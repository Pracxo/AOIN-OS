from __future__ import annotations

import pytest
from pydantic import ValidationError

from aion_brain.contracts.production_auth import (
    PROHIBITED_RUNTIME_FIELDS,
    ProductionAuthCoreConfig,
)


@pytest.mark.parametrize("field_name", PROHIBITED_RUNTIME_FIELDS)
def test_every_prohibited_production_auth_setting_true_fails_closed(field_name: str) -> None:
    payload = ProductionAuthCoreConfig().model_dump()

    with pytest.raises(ValidationError):
        ProductionAuthCoreConfig(**{**payload, field_name: True})


def test_config_matrix_defaults_keep_all_prohibited_settings_false() -> None:
    config = ProductionAuthCoreConfig()

    for field_name in PROHIBITED_RUNTIME_FIELDS:
        assert getattr(config, field_name) is False
