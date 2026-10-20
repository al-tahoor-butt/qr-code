"""
Data models and configuration schemas for QR Architect.
"""

from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, Field


class ModuleStyle(str, Enum):
    SQUARE = "square"
    ROUNDED = "rounded"
    CIRCLE = "circle"
    GAPPED = "gapped"


class EyeStyle(str, Enum):
    SQUARE = "square"
    ROUNDED = "rounded"
    CIRCLE = "circle"


class GradientType(str, Enum):
    NONE = "none"
    LINEAR_VERTICAL = "linear_vertical"
    LINEAR_HORIZONTAL = "linear_horizontal"
    LINEAR_DIAGONAL = "linear_diagonal"
    RADIAL = "radial"


class LogoShape(str, Enum):
    CIRCLE = "circle"
    ROUNDED = "rounded"
    SQUARE = "square"
    ORIGINAL = "original"


class ErrorCorrection(str, Enum):
    L = "L"  # ~7% recovery
    M = "M"  # ~15% recovery
    Q = "Q"  # ~25% recovery
    H = "H"  # ~30% recovery (Mandatory/recommended for embedded images)


class ColorConfig(BaseModel):
    front_color: str = Field(default="#0f172a", description="Foreground module color (hex e.g. #0f172a)")
    back_color: str = Field(default="#ffffff", description="Background color (hex e.g. #ffffff or 'transparent')")
    gradient_type: GradientType = Field(default=GradientType.NONE, description="Gradient fill style")
    gradient_end_color: Optional[str] = Field(default=None, description="End color for gradient")
    eye_outer_color: Optional[str] = Field(default=None, description="Outer finder frame color")
    eye_inner_color: Optional[str] = Field(default=None, description="Inner finder center dot color")


class LogoConfig(BaseModel):
    image_path: Optional[str] = Field(default=None, description="Path to logo image file")
    image_base64: Optional[str] = Field(default=None, description="Base64 encoded logo image data")
    scale: float = Field(default=0.22, ge=0.08, le=0.30, description="Logo dimension as fraction of QR code (0.08 to 0.30)")
    shape: LogoShape = Field(default=LogoShape.CIRCLE, description="Shape mask for embedded logo")
    padding: int = Field(default=4, ge=0, le=20, description="Padding / quiet margin around logo in pixels")
    bg_color: str = Field(default="#ffffff", description="Background color for logo cutout pad")


class QRConfig(BaseModel):
    data: str = Field(..., description="Link, URL, or textual data payload to encode")
    colors: ColorConfig = Field(default_factory=ColorConfig, description="Color palette and gradient setup")
    module_style: ModuleStyle = Field(default=ModuleStyle.ROUNDED, description="Shape of body data modules")
    eye_style: EyeStyle = Field(default=EyeStyle.ROUNDED, description="Shape of the 3 corner finder eyes")
    error_correction: ErrorCorrection = Field(default=ErrorCorrection.H, description="Reed-Solomon error correction level")
    logo: Optional[LogoConfig] = Field(default=None, description="Optional embedded logo configuration")
    box_size: int = Field(default=12, ge=4, le=40, description="Pixel size per QR module")
    border: int = Field(default=4, ge=1, le=10, description="Module quiet zone border width")
    format: str = Field(default="PNG", description="Output format: PNG, SVG, JPEG, WEBP")
    auto_verify: bool = Field(default=True, description="Automatically decode and verify link retention after generation")


class ValidationReport(BaseModel):
    is_valid: bool = Field(..., description="True if barcode was successfully detected and decoded")
    decoded_text: Optional[str] = Field(default=None, description="Extracted payload decoded from the QR image")
    matches_payload: bool = Field(..., description="True if decoded text strictly matches the original requested link")
    error_correction: str = Field(..., description="Applied error correction level")
    logo_coverage_pct: float = Field(..., description="Percentage of QR area covered by embedded logo")
    contrast_ratio: float = Field(..., description="Calculated WCAG luminance contrast ratio")
    warnings: List[str] = Field(default_factory=list, description="List of warnings or potential scanning risks")
    recommendations: List[str] = Field(default_factory=list, description="Guidance to improve scannability if needed")


class GenerationResult(BaseModel):
    image_base64: Optional[str] = Field(default=None, description="Base64 data URI of the generated image (for raster)")
    svg_content: Optional[str] = Field(default=None, description="Raw SVG text content (for vector)")
    format: str = Field(..., description="Generated file format")
    width: int = Field(..., description="Image width in pixels")
    height: int = Field(..., description="Image height in pixels")
    validation: ValidationReport = Field(..., description="Scannability and link retention verification report")
