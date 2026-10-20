"""
QR Architect - Production architecture for customizable QR code generation
with embedded logos and automated link retention verification.
"""

from qr_architect.models import (
    QRConfig,
    ColorConfig,
    LogoConfig,
    ModuleStyle,
    EyeStyle,
    GradientType,
    LogoShape,
    ErrorCorrection,
    ValidationReport,
    GenerationResult
)
from qr_architect.generator import generate_qr, generate_qr_raster, generate_qr_svg
from qr_architect.validator import verify_qr_image, calculate_contrast_ratio
from qr_architect.presets import PRESETS, get_preset

__version__ = "1.0.0"
__all__ = [
    "generate_qr",
    "generate_qr_raster",
    "generate_qr_svg",
    "verify_qr_image",
    "calculate_contrast_ratio",
    "QRConfig",
    "ColorConfig",
    "LogoConfig",
    "ModuleStyle",
    "EyeStyle",
    "GradientType",
    "LogoShape",
    "ErrorCorrection",
    "ValidationReport",
    "GenerationResult",
    "PRESETS",
    "get_preset"
]
