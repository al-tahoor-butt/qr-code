"""
Example 2: Embedding an Image/Logo while Retaining Full Link Integrity.
"""

import os
from qr_architect import (
    QRConfig,
    ColorConfig,
    LogoConfig,
    LogoShape,
    ModuleStyle,
    EyeStyle,
    ErrorCorrection,
    generate_qr
)

def main():
    logo_file = os.path.join(os.path.dirname(__file__), "sample_logo.png")

    config = QRConfig(
        data="https://antigravity.google.com/enterprise",
        colors=ColorConfig(
            front_color="#0f172a",
            back_color="#ffffff",
            eye_outer_color="#4338ca",
            eye_inner_color="#06b6d4"
        ),
        module_style=ModuleStyle.ROUNDED,
        eye_style=EyeStyle.ROUNDED,
        # Mandatory high error correction for embedded images
        error_correction=ErrorCorrection.H,
        logo=LogoConfig(
            image_path=logo_file,
            scale=0.22,           # 22% scale is well within the 30% safe threshold
            shape=LogoShape.CIRCLE,
            padding=4,            # 4px quiet margin around logo to avoid module bleed
            bg_color="#ffffff"
        ),
        box_size=14
    )

    result = generate_qr(config)
    val = result.validation

    print(f"Generated QR with Logo: {result.width}x{result.height}px")
    print(f"Scannable?            : {val.is_valid}")
    print(f"Decoded Link          : {val.decoded_text}")
    print(f"Link Retained?        : {val.matches_payload}")
    print(f"Logo Coverage         : {val.logo_coverage_pct}%")
    print(f"Error Correction Mode : Level {val.error_correction}")

    assert val.matches_payload, "Decoded link must match input!"
    print("✓ Success! Image embedded and link remains 100% scannable.")

if __name__ == "__main__":
    main()
