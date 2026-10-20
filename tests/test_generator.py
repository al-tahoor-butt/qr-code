"""
Unit tests for QR Generator engine.
"""

import os
from qr_architect.models import (
    QRConfig,
    ColorConfig,
    LogoConfig,
    LogoShape,
    ModuleStyle,
    EyeStyle,
    GradientType,
    ErrorCorrection
)
from qr_architect.generator import generate_qr, generate_qr_svg


def test_basic_generation():
    config = QRConfig(data="https://example.com/test-1")
    result = generate_qr(config)
    assert result.image_base64 is not None
    assert result.width > 0
    assert result.height > 0
    assert result.validation.is_valid is True
    assert result.validation.matches_payload is True


def test_custom_colors_and_styles():
    for m_style in [ModuleStyle.SQUARE, ModuleStyle.ROUNDED, ModuleStyle.CIRCLE, ModuleStyle.GAPPED]:
        for e_style in [EyeStyle.SQUARE, EyeStyle.ROUNDED, EyeStyle.CIRCLE]:
            config = QRConfig(
                data=f"https://example.com/style-{m_style.value}-{e_style.value}",
                colors=ColorConfig(
                    front_color="#1e293b",
                    back_color="#ffffff",
                    eye_outer_color="#4338ca",
                    eye_inner_color="#06b6d4"
                ),
                module_style=m_style,
                eye_style=e_style
            )
            result = generate_qr(config)
            assert result.validation.is_valid is True, f"Failed for styles {m_style}, {e_style}"
            assert result.validation.matches_payload is True


def test_gradients():
    for g_type in [
        GradientType.LINEAR_HORIZONTAL,
        GradientType.LINEAR_VERTICAL,
        GradientType.LINEAR_DIAGONAL,
        GradientType.RADIAL
    ]:
        config = QRConfig(
            data="https://example.com/gradient-test",
            colors=ColorConfig(
                front_color="#1e3a8a",
                back_color="#ffffff",
                gradient_type=g_type,
                gradient_end_color="#7c3aed"
            )
        )
        result = generate_qr(config)
        assert result.validation.is_valid is True, f"Gradient {g_type} failed validation"
        assert result.validation.matches_payload is True


def test_svg_export():
    config = QRConfig(
        data="https://example.com/svg-test",
        format="SVG",
        colors=ColorConfig(
            front_color="#0f172a",
            gradient_type=GradientType.LINEAR_DIAGONAL,
            gradient_end_color="#2563eb"
        )
    )
    result = generate_qr(config)
    assert result.svg_content is not None
    assert result.svg_content.startswith("<svg")
    assert "</svg>" in result.svg_content
    assert result.validation.matches_payload is True


def test_logo_embedding_retains_link():
    logo_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "examples", "sample_logo.png")
    config = QRConfig(
        data="https://antigravity.google.com/verify-retention",
        colors=ColorConfig(
            front_color="#0f172a",
            back_color="#ffffff",
            eye_outer_color="#1d4ed8",
            eye_inner_color="#0284c7"
        ),
        error_correction=ErrorCorrection.H,
        logo=LogoConfig(
            image_path=logo_path,
            scale=0.22,
            shape=LogoShape.CIRCLE,
            padding=4,
            bg_color="#ffffff"
        )
    )
    result = generate_qr(config)
    assert result.validation.is_valid is True
    assert result.validation.matches_payload is True
    assert result.validation.decoded_text == "https://antigravity.google.com/verify-retention"
