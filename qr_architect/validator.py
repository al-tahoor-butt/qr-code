"""
Validator module for testing QR code scannability and ensuring link retention.
"""

import math
from typing import Optional, List, Tuple
from PIL import Image, ImageColor
import zxingcpp

from qr_architect.models import ValidationReport, ErrorCorrection, QRConfig


def parse_color_rgb(color_str: str) -> Tuple[int, int, int]:
    """Parse a hex or css color string to (R, G, B)."""
    if not color_str or color_str.lower() in ("transparent", "none"):
        return (255, 255, 255)
    try:
        rgba = ImageColor.getrgb(color_str)
        return (rgba[0], rgba[1], rgba[2])
    except Exception:
        return (0, 0, 0)


def relative_luminance(rgb: Tuple[int, int, int]) -> float:
    """Calculate relative luminance per WCAG 2.1 specs."""
    def channel_lum(c: int) -> float:
        v = c / 255.0
        return v / 12.92 if v <= 0.03928 else math.pow((v + 0.055) / 1.055, 2.4)
    r, g, b = rgb
    return 0.2126 * channel_lum(r) + 0.7152 * channel_lum(g) + 0.0722 * channel_lum(b)


def calculate_contrast_ratio(c1: str, c2: str) -> float:
    """Calculate contrast ratio between two colors (1.0 to 21.0)."""
    l1 = relative_luminance(parse_color_rgb(c1))
    l2 = relative_luminance(parse_color_rgb(c2))
    lighter = max(l1, l2)
    darker = min(l1, l2)
    return round((lighter + 0.05) / (darker + 0.05), 2)


def verify_qr_image(
    image: Image.Image,
    expected_data: str,
    config: Optional[QRConfig] = None
) -> ValidationReport:
    """
    Decodes the QR code image using zxing-cpp and verifies link retention,
    measuring contrast and error correction safety margins.
    """
    warnings: List[str] = []
    recommendations: List[str] = []

    # Prepare image for decoding: composite transparent images onto white background
    if image.mode in ("RGBA", "LA") or (image.mode == "P" and "transparency" in image.info):
        alpha_img = image.convert("RGBA")
        background = Image.new("RGBA", alpha_img.size, (255, 255, 255, 255))
        composite = Image.alpha_composite(background, alpha_img)
        decode_img = composite.convert("RGB")
    else:
        decode_img = image.convert("RGB")

    # Run barcode reader
    read_result = zxingcpp.read_barcode(decode_img)
    is_valid = read_result is not None
    decoded_text = read_result.text if read_result else None
    matches_payload = (decoded_text == expected_data) if (decoded_text and expected_data) else False

    # Calculate contrast
    fg = config.colors.front_color if config else "#000000"
    bg = config.colors.back_color if config else "#ffffff"
    contrast = calculate_contrast_ratio(fg, bg)

    if contrast < 3.0:
        warnings.append(f"Low contrast ratio ({contrast}:1). Barcode scanners usually require >= 4.5:1.")
        recommendations.append("Increase contrast between foreground and background colors for reliable mobile scanning.")
    elif contrast < 4.5:
        warnings.append(f"Moderate contrast ratio ({contrast}:1). May have difficulty scanning in low light.")

    # Calculate logo coverage
    logo_coverage_pct = 0.0
    ecc_level = (config.error_correction.value if config else "H")

    if config and config.logo:
        scale = config.logo.scale
        logo_coverage_pct = round((scale ** 2) * 100, 2)

        max_safe_by_ecc = {
            "L": 5.0,
            "M": 12.0,
            "Q": 20.0,
            "H": 28.0
        }
        safe_limit = max_safe_by_ecc.get(ecc_level, 25.0)

        if logo_coverage_pct > safe_limit:
            warnings.append(
                f"Logo coverage ({logo_coverage_pct}%) exceeds recommended safe margin ({safe_limit}%) for ECC {ecc_level}."
            )
            recommendations.append(
                f"Reduce logo scale to <= 0.22 or use Error Correction Level H to retain link integrity."
            )

        if ecc_level != "H" and ecc_level != "Q":
            warnings.append(f"Error correction level '{ecc_level}' is low for embedded images.")
            recommendations.append("Always use Error Correction Level H (30%) when embedding a logo.")

    # Check scannability result
    if not is_valid:
        warnings.append("Barcode scanner could not detect or decode any QR pattern in this image.")
        if contrast < 4.0:
            recommendations.append("The primary cause is insufficient color contrast between modules and background.")
        if logo_coverage_pct > 20.0:
            recommendations.append("The embedded logo may be obscuring too many modules or finder patterns.")
    elif not matches_payload:
        warnings.append("QR code decoded, but the extracted content does not match the requested link!")
        recommendations.append("Check for character encoding or truncation issues in the payload.")

    return ValidationReport(
        is_valid=is_valid,
        decoded_text=decoded_text,
        matches_payload=matches_payload,
        error_correction=ecc_level,
        logo_coverage_pct=logo_coverage_pct,
        contrast_ratio=contrast,
        warnings=warnings,
        recommendations=recommendations
    )
