"""Authorization exports for external cognition."""

from aion_brain.contracts.external_cognition import ExternalCognitionAuthorizationEnvelope
from aion_brain.external_cognition.integrity import create_default_authorization

__all__ = ["ExternalCognitionAuthorizationEnvelope", "create_default_authorization"]
