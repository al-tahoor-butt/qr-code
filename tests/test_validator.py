"""
Unit tests for QR Validator and scannability verification.
"""

from qr_architect.validator import calculate_contrast_ratio, verify_qr_image
from qr_architect.models import QRConfig, ColorConfig, LogoConfig, ErrorCorrection
from qr_architect.generator import generate_qr_raster


def test_contrast_ratio_calculation():
    # Pure black on pure white -> 21:1
    assert calculate_contrast_ratio("#000000", "#ffffff") == 21.0
    # Same color -> 1:1
    assert calculate_contrast_ratio("#ffffff", "#ffffff") == 1.0
    # Low contrast: yellow on white
    low = calculate_contrast_ratio("#ffff00", "#ffffff")
    assert low < 3.0


def test_validator_detects_low_contrast():
    config = QRConfig(
        data="https://example.com/contrast-warning",
        colors=ColorConfig(
            front_color="#ffff00", # Yellow on white has terrible contrast
            back_color="#ffffff"
        )
    )
    img = generate_qr_raster(config)
    report = verify_qr_image(img, config.data, config)
    # Must report low contrast warnings
    assert any("Low contrast" in w for w in report.warnings)


def test_validator_warns_on_oversized_logo_for_low_ecc():
    config = QRConfig(
        data="https://example.com/oversized-logo",
        error_correction=ErrorCorrection.L, # Level L cannot support 25% logo
        logo=LogoConfig(
            scale=0.25
        )
    )
    # Coverage for 0.25 is 6.25%, which exceeds Level L limit (5.0%)
    img = generate_qr_raster(config)
    report = verify_qr_image(img, config.data, config)
    assert any("exceeds recommended safe margin" in w for w in report.warnings)
