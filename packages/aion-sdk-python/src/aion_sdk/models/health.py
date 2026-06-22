"""Health models."""

from aion_sdk.models.base import AIONSDKModel


class HealthModel(AIONSDKModel):
    status: str
    service: str
    version: str


class ReadinessModel(AIONSDKModel):
    status: str
    checks: dict[str, str]
