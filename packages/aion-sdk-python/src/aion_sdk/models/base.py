"""Base SDK model."""

from typing import Any

from pydantic import BaseModel, ConfigDict


class AIONSDKModel(BaseModel):
    """Forward-compatible model for public AION contracts."""

    model_config = ConfigDict(extra="allow")


Metadata = dict[str, Any]
