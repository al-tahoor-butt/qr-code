"""
Example 3: Generating Multi-Color Gradient QR Codes (PNG and SVG vector).
"""

from qr_architect import (
    QRConfig,
    ColorConfig,
    GradientType,
    ModuleStyle,
    EyeStyle,
    generate_qr
)

def main():
    config = QRConfig(
        data="https://antigravity.google.com/showcase",
        colors=ColorConfig(
            front_color="#e11d48",                    # Rose start
            back_color="#ffffff",
            gradient_type=GradientType.LINEAR_DIAGONAL,
            gradient_end_color="#7c3aed",             # Violet end
            eye_outer_color="#be123c",
            eye_inner_color="#6d28d9"
        ),
        module_style=ModuleStyle.ROUNDED,
        eye_style=EyeStyle.ROUNDED,
        format="SVG",
        box_size=12
    )

    # 1. Vector SVG Generation
    svg_result = generate_qr(config)
    print("SVG Generation Successful:")
    print(f"  SVG Length    : {len(svg_result.svg_content)} bytes")
    print(f"  Link Retained : {svg_result.validation.matches_payload}")

    # 2. Raster PNG Generation
    config.format = "PNG"
    png_result = generate_qr(config)
    print("\nPNG Generation Successful:")
    print(f"  Dimensions    : {png_result.width}x{png_result.height}")
    print(f"  Decoded Text  : {png_result.validation.decoded_text}")
    print(f"  Contrast      : {png_result.validation.contrast_ratio}:1")

    assert png_result.validation.matches_payload
    print("✓ Success! Gradient QR codes verified successfully.")

if __name__ == "__main__":
    main()
