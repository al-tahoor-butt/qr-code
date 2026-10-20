"""
Command Line Interface for QR Architect.
"""

import argparse
import sys
import os
import getpass
import base64
from PIL import Image

from qr_architect.models import (
    QRConfig,
    ColorConfig,
    LogoConfig,
    ModuleStyle,
    EyeStyle,
    GradientType,
    LogoShape,
    ErrorCorrection
)
from qr_architect.generator import generate_qr
from qr_architect.validator import verify_qr_image
from qr_architect.presets import PRESETS, get_preset
from qr_architect.auth import hash_password, get_configured_password_hash


def handle_generate(args):
    """Handle QR code generation command."""
    preset_data = {}
    if args.preset:
        if args.preset in PRESETS:
            preset_data = get_preset(args.preset)
            print(f"Applied preset: {preset_data.get('name')}")
        else:
            print(f"Unknown preset '{args.preset}'. Available: {', '.join(PRESETS.keys())}")
            sys.exit(1)

    colors_dict = preset_data.get("colors", {})
    front_color = args.fg or colors_dict.get("front_color", "#0f172a")
    back_color = args.bg or colors_dict.get("back_color", "#ffffff")
    gradient_type = GradientType(args.gradient) if args.gradient else colors_dict.get("gradient_type", GradientType.NONE)
    gradient_end_color = args.gradient_end or colors_dict.get("gradient_end_color")
    eye_outer_color = args.eye_outer or colors_dict.get("eye_outer_color")
    eye_inner_color = args.eye_inner or colors_dict.get("eye_inner_color")

    module_style = ModuleStyle(args.module_style) if args.module_style else preset_data.get("module_style", ModuleStyle.ROUNDED)
    eye_style = EyeStyle(args.eye_style) if args.eye_style else preset_data.get("eye_style", EyeStyle.ROUNDED)
    ecc = ErrorCorrection(args.ecc) if args.ecc else preset_data.get("error_correction", ErrorCorrection.H)

    logo_cfg = None
    if args.logo:
        if not os.path.exists(args.logo):
            print(f"Error: Logo file not found: {args.logo}")
            sys.exit(1)
        logo_cfg = LogoConfig(
            image_path=args.logo,
            scale=args.logo_scale,
            shape=LogoShape(args.logo_shape),
            padding=args.logo_padding,
            bg_color=args.logo_bg
        )

    output_path = args.output
    fmt = args.format.upper()
    if output_path:
        ext = os.path.splitext(output_path)[1].lower()
        if ext == ".svg":
            fmt = "SVG"
        elif ext in (".jpg", ".jpeg"):
            fmt = "JPEG"
        elif ext == ".webp":
            fmt = "WEBP"
        elif ext == ".png":
            fmt = "PNG"

    config = QRConfig(
        data=args.data,
        colors=ColorConfig(
            front_color=front_color,
            back_color=back_color,
            gradient_type=gradient_type,
            gradient_end_color=gradient_end_color,
            eye_outer_color=eye_outer_color,
            eye_inner_color=eye_inner_color
        ),
        module_style=module_style,
        eye_style=eye_style,
        error_correction=ecc,
        logo=logo_cfg,
        box_size=args.box_size,
        border=args.border,
        format=fmt
    )

    result = generate_qr(config)
    val = result.validation

    default_out = f"qrcode.{fmt.lower()}"
    save_path = output_path or default_out

    if fmt == "SVG":
        with open(save_path, "w", encoding="utf-8") as f:
            f.write(result.svg_content)
    else:
        raw_b64 = result.image_base64.split(",", 1)[1]
        data = base64.b64decode(raw_b64)
        with open(save_path, "wb") as f:
            f.write(data)

    print(f"\nSuccessfully generated QR code -> {save_path} ({result.width}x{result.height})")
    print("-" * 55)
    print("LINK INTEGRITY & SCANNABILITY REPORT:")
    print(f"  Scannable       : {'YES' if val.is_valid else 'NO'}")
    print(f"  Decoded Link    : {val.decoded_text}")
    print(f"  Matches Input   : {'YES' if val.matches_payload else 'NO'}")
    print(f"  ECC Level       : {val.error_correction}")
    print(f"  Contrast Ratio  : {val.contrast_ratio}:1")
    if val.logo_coverage_pct > 0:
        print(f"  Logo Coverage   : {val.logo_coverage_pct}%")

    if val.warnings:
        print("\nWarnings:")
        for w in val.warnings:
            print(f"  ! {w}")

    if val.recommendations:
        print("\nRecommendations:")
        for r in val.recommendations:
            print(f"  * {r}")
    print("-" * 55)

    if not val.is_valid or not val.matches_payload:
        sys.exit(2)


def handle_verify(args):
    """Handle QR code image verification."""
    if not os.path.exists(args.image):
        print(f"Error: File not found: {args.image}")
        sys.exit(1)

    try:
        img = Image.open(args.image)
    except Exception as e:
        print(f"Error reading image: {e}")
        sys.exit(1)

    expected = args.expected or ""
    report = verify_qr_image(img, expected)

    print("-" * 55)
    print(f"SCANNING FILE: {args.image}")
    print(f"  Detected QR Code : {'YES' if report.is_valid else 'NO'}")
    print(f"  Decoded Content  : {report.decoded_text}")
    if expected:
        print(f"  Expected Content : {expected}")
        print(f"  Matches Expected : {'YES' if report.matches_payload else 'NO'}")
    print(f"  Contrast Ratio   : {report.contrast_ratio}:1")

    if report.warnings:
        print("\nWarnings:")
        for w in report.warnings:
            print(f"  ! {w}")
    print("-" * 55)

    if not report.is_valid or (expected and not report.matches_payload):
        sys.exit(2)


def handle_presets(args):
    """List available design presets."""
    print("\nAVAILABLE DESIGN PRESETS:")
    print("=" * 60)
    for key, info in PRESETS.items():
        print(f"\n* Preset Key: '{key}' ({info['name']})")
        print(f"  Description: {info['description']}")
        print(f"  Colors     : Foreground={info['colors']['front_color']}, Background={info['colors']['back_color']}")
        if info['colors'].get('gradient_type') != GradientType.NONE:
            print(f"  Gradient   : {info['colors'].get('gradient_type')} -> {info['colors'].get('gradient_end_color')}")
        print(f"  Module/Eye : {info['module_style'].value} / {info['eye_style'].value}")
    print("\nUse with: python -m qr_architect.cli generate --data <link> --preset <key>\n")


def handle_set_password(args):
    """Hash and set new access password."""
    password = args.password
    if not password:
        password = getpass.getpass("Enter new splash screen password: ")
        confirm = getpass.getpass("Confirm password: ")
        if password != confirm:
            print("Error: Passwords do not match.")
            sys.exit(1)

    if len(password) < 4:
        print("Error: Password should be at least 4 characters.")
        sys.exit(1)

    hashed = hash_password(password)
    print("\n✓ Salted PBKDF2 hash generated:")
    print(f"  {hashed}")

    # Optionally write to .env
    env_file = ".env"
    lines = []
    if os.path.exists(env_file):
        with open(env_file, "r") as f:
            lines = [l for l in f.readlines() if not l.startswith("APP_PASSWORD_HASH=")]

    lines.append(f"APP_PASSWORD_HASH={hashed}\n")
    with open(env_file, "w") as f:
        f.writelines(lines)

    print(f"✓ Saved to {env_file}")
    print("Restart the server to apply the new password.\n")


def handle_serve(args):
    """Start the FastAPI server + Web Dashboard."""
    import uvicorn
    from qr_architect.api import app

    # Check password config
    h = get_configured_password_hash()
    print("=" * 60)
    print("  QR ARCHITECT SERVER WITH SPLASH SCREEN AUTHENTICATION")
    print("=" * 60)
    if "qr-admin-2026" in os.environ.get("APP_PASSWORD", "qr-admin-2026") and not os.environ.get("APP_PASSWORD_HASH"):
        print("  NOTICE: Using default splash password: 'qr-admin-2026'")
        print("  To change, run: ./qr_gen set-password")
    else:
        print("  STATUS: Custom salted/hashed password configured.")

    print(f"  URL   : http://{args.host}:{args.port}")
    print(f"  DOCS  : http://{args.host}:{args.port}/docs")
    print("=" * 60 + "\n")

    uvicorn.run(app, host=args.host, port=args.port)


def main():
    parser = argparse.ArgumentParser(
        prog="qr-gen",
        description="QR Architect: High-fidelity QR code generation with color styling, image embedding, and link verification."
    )
    subparsers = parser.add_subparsers(dest="command", help="Sub-commands")

    # Generate command
    gen_parser = subparsers.add_parser("generate", help="Generate a customized QR code")
    gen_parser.add_argument("--data", "-d", required=True, help="URL, link, or text to encode")
    gen_parser.add_argument("--output", "-o", help="Target output file path (e.g. output.png, code.svg)")
    gen_parser.add_argument("--preset", "-p", help="Aesthetic preset name (e.g. modern_tech, sunset_glow)")
    gen_parser.add_argument("--fg", help="Foreground color (hex e.g. '#1e40af')")
    gen_parser.add_argument("--bg", default="#ffffff", help="Background color (hex or 'transparent')")
    gen_parser.add_argument("--gradient", choices=[g.value for g in GradientType], help="Gradient type")
    gen_parser.add_argument("--gradient-end", help="Gradient end color")
    gen_parser.add_argument("--eye-outer", help="Eye outer frame color")
    gen_parser.add_argument("--eye-inner", help="Eye inner ball color")
    gen_parser.add_argument("--module-style", choices=[m.value for m in ModuleStyle], help="Module shape")
    gen_parser.add_argument("--eye-style", choices=[e.value for e in EyeStyle], help="Eye shape")
    gen_parser.add_argument("--ecc", choices=[e.value for e in ErrorCorrection], default="H", help="Error correction level")
    gen_parser.add_argument("--logo", help="Path to logo image to embed in center")
    gen_parser.add_argument("--logo-shape", choices=[s.value for s in LogoShape], default="circle", help="Logo mask shape")
    gen_parser.add_argument("--logo-scale", type=float, default=0.22, help="Logo size fraction (0.08 to 0.28, default 0.22)")
    gen_parser.add_argument("--logo-padding", type=int, default=4, help="Logo quiet zone padding pixels")
    gen_parser.add_argument("--logo-bg", default="#ffffff", help="Logo padding background color")
    gen_parser.add_argument("--box-size", type=int, default=12, help="Pixels per module (default 12)")
    gen_parser.add_argument("--border", type=int, default=4, help="Border quiet modules (default 4)")
    gen_parser.add_argument("--format", choices=["PNG", "SVG", "JPEG", "WEBP"], default="PNG", help="Output file format")

    # Verify command
    verify_parser = subparsers.add_parser("verify", help="Verify scannability and link retention of an existing QR image")
    verify_parser.add_argument("image", help="Path to QR code image file")
    verify_parser.add_argument("--expected", "-e", help="Expected URL/payload to check against")

    # Presets command
    subparsers.add_parser("presets", help="List available design presets")

    # Set-password command
    pwd_parser = subparsers.add_parser("set-password", help="Hash and configure new access password")
    pwd_parser.add_argument("--password", "-p", help="New plaintext password to hash")

    # Serve command
    serve_parser = subparsers.add_parser("serve", help="Launch the Web UI and API service")
    serve_parser.add_argument("--host", default="0.0.0.0", help="Host address (default: 0.0.0.0)")
    serve_parser.add_argument("--port", type=int, default=8000, help="Port (default: 8000)")

    args = parser.parse_args()

    if args.command == "generate":
        handle_generate(args)
    elif args.command == "verify":
        handle_verify(args)
    elif args.command == "presets":
        handle_presets(args)
    elif args.command == "set-password":
        handle_set_password(args)
    elif args.command == "serve":
        handle_serve(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
