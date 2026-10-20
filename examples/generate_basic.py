"""
Example 1: Basic Custom Colored QR Code with Scannability Verification.
"""

from qr_architect import QRConfig, ColorConfig, ModuleStyle, EyeStyle, generate_qr

def main():
    config = QRConfig(
        data="https://antigravity.google.com/docs",
        colors=ColorConfig(
            front_color="#1e3a8a",       # Deep corporate blue
            back_color="#f8fafc",        # Soft light background
            eye_outer_color="#1d4ed8",   # Vibrant blue outer eye frame
            eye_inner_color="#0284c7"    # Sky blue inner eye ball
        ),
        module_style=ModuleStyle.ROUNDED,
        eye_style=EyeStyle.ROUNDED,
        box_size=12
    )

    result = generate_qr(config)
    val = result.validation

    print(f"Generated QR Code: {result.width}x{result.height}px")
    print(f"Scannable?       : {val.is_valid}")
    print(f"Decoded Link     : {val.decoded_text}")
    print(f"Link Retained?   : {val.matches_payload}")
    print(f"Contrast Ratio   : {val.contrast_ratio}:1")

    assert val.matches_payload, "Decoded link must match input!"
    print("✓ Success! Link integrity fully retained.")

if __name__ == "__main__":
    main()
