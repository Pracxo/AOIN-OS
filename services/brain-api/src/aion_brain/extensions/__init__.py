"""AION Extension Registry metadata-only services."""

from aion_brain.extensions.capabilities import CapabilityDeclarationService
from aion_brain.extensions.compatibility_gate import ExtensionCompatibilityGate
from aion_brain.extensions.dependencies import DependencyDeclarationService
from aion_brain.extensions.install_plans import InstallPlanService
from aion_brain.extensions.intake import ExtensionIntakeService
from aion_brain.extensions.manifest_validator import ManifestValidator
from aion_brain.extensions.packages import ExtensionPackageService
from aion_brain.extensions.query import ExtensionQueryService
from aion_brain.extensions.repository import ExtensionRegistryRepository
from aion_brain.extensions.reviews import ExtensionReviewService

__all__ = [
    "CapabilityDeclarationService",
    "DependencyDeclarationService",
    "ExtensionCompatibilityGate",
    "ExtensionIntakeService",
    "ExtensionPackageService",
    "ExtensionQueryService",
    "ExtensionRegistryRepository",
    "ExtensionReviewService",
    "InstallPlanService",
    "ManifestValidator",
]
