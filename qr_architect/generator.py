"""
QR Code Generator engine supporting custom colors, gradients, eye shapes,
safe logo embedding, vector SVG and high-resolution raster export.
"""

import base64
import io
import math
from typing import Tuple, Optional
from PIL import Image, ImageDraw, ImageColor, ImageFilter
import qrcode
from qrcode.constants import ERROR_CORRECT_L, ERROR_CORRECT_M, ERROR_CORRECT_Q, ERROR_CORRECT_H

from qr_architect.models import (
    QRConfig,
    GenerationResult,
    ModuleStyle,
    EyeStyle,
    GradientType,
    LogoShape,
    ErrorCorrection,
)
from qr_architect.validator import verify_qr_image, parse_color_rgb


ECC_MAP = {
    ErrorCorrection.L: ERROR_CORRECT_L,
    ErrorCorrection.M: ERROR_CORRECT_M,
    ErrorCorrection.Q: ERROR_CORRECT_Q,
    ErrorCorrection.H: ERROR_CORRECT_H,
}


def parse_color_rgba(color_str: str) -> Tuple[int, int, int, int]:
    """Parse color into RGBA tuple, handling 'transparent'."""
    if not color_str or color_str.lower() in ("transparent", "none"):
        return (255, 255, 255, 0)
    try:
        rgb = ImageColor.getrgb(color_str)
        if len(rgb) == 4:
            return rgb
        return (rgb[0], rgb[1], rgb[2], 255)
    except Exception:
        return (0, 0, 0, 255)


def interpolate_color(c1: Tuple[int, int, int], c2: Tuple[int, int, int], t: float) -> Tuple[int, int, int, int]:
    """Interpolate between two RGB colors with clamped factor t in [0, 1]."""
    t = max(0.0, min(1.0, t))
    r = int(c1[0] + (c2[0] - c1[0]) * t)
    g = int(c1[1] + (c2[1] - c1[1]) * t)
    b = int(c1[2] + (c2[2] - c1[2]) * t)
    return (r, g, b, 255)


def get_module_color(
    row: int,
    col: int,
    grid_size: int,
    total_size: int,
    box_size: int,
    border: int,
    c_start: Tuple[int, int, int],
    c_end: Tuple[int, int, int],
    grad_type: GradientType
) -> Tuple[int, int, int, int]:
    """Compute color for a module given gradient settings."""
    if grad_type == GradientType.NONE:
        return (c_start[0], c_start[1], c_start[2], 255)

    x = (col + border) * box_size + box_size / 2.0
    y = (row + border) * box_size + box_size / 2.0

    if grad_type == GradientType.LINEAR_HORIZONTAL:
        t = x / total_size
    elif grad_type == GradientType.LINEAR_VERTICAL:
        t = y / total_size
    elif grad_type == GradientType.LINEAR_DIAGONAL:
        t = (x + y) / (2.0 * total_size)
    elif grad_type == GradientType.RADIAL:
        cx, cy = total_size / 2.0, total_size / 2.0
        dist = math.sqrt((x - cx) ** 2 + (y - cy) ** 2)
        max_dist = math.sqrt(2.0) * (total_size / 2.0)
        t = dist / max_dist
    else:
        t = 0.0

    return interpolate_color(c_start, c_end, t)


def load_logo_image(logo_config) -> Optional[Image.Image]:
    """Load logo image from path or base64 string."""
    if not logo_config:
        return None

    if logo_config.image_path:
        try:
            return Image.open(logo_config.image_path).convert("RGBA")
        except Exception as e:
            print(f"Warning: Failed to load logo from path {logo_config.image_path}: {e}")

    if logo_config.image_base64:
        try:
            raw_b64 = logo_config.image_base64
            if "," in raw_b64:
                raw_b64 = raw_b64.split(",", 1)[1]
            data = base64.b64decode(raw_b64)
            return Image.open(io.BytesIO(data)).convert("RGBA")
        except Exception as e:
            print(f"Warning: Failed to decode base64 logo: {e}")

    return None


def mask_logo(logo: Image.Image, shape: LogoShape) -> Image.Image:
    """Apply a circular or rounded mask to the logo."""
    w, h = logo.size
    min_dim = min(w, h)
    # Crop to square first
    left = (w - min_dim) // 2
    top = (h - min_dim) // 2
    logo_square = logo.crop((left, top, left + min_dim, top + min_dim))
    dim = logo_square.size[0]

    if shape == LogoShape.CIRCLE:
        mask = Image.new("L", (dim * 4, dim * 4), 0)
        draw = ImageDraw.Draw(mask)
        draw.ellipse([0, 0, dim * 4 - 1, dim * 4 - 1], fill=255)
        mask = mask.resize((dim, dim), Image.Resampling.LANCZOS)
        logo_square.putalpha(mask)
    elif shape == LogoShape.ROUNDED:
        mask = Image.new("L", (dim * 4, dim * 4), 0)
        draw = ImageDraw.Draw(mask)
        draw.rounded_rectangle([0, 0, dim * 4 - 1, dim * 4 - 1], radius=int(dim * 4 * 0.22), fill=255)
        mask = mask.resize((dim, dim), Image.Resampling.LANCZOS)
        logo_square.putalpha(mask)

    return logo_square


def is_finder_module(row: int, col: int, grid_size: int) -> bool:
    """Return True if (row, col) is within any of the 3 corner finder patterns (7x7 modules)."""
    # Top-Left (0..6, 0..6)
    if 0 <= row < 7 and 0 <= col < 7:
        return True
    # Top-Right (0..6, N-7..N-1)
    if 0 <= row < 7 and grid_size - 7 <= col < grid_size:
        return True
    # Bottom-Left (N-7..N-1, 0..6)
    if grid_size - 7 <= row < grid_size and 0 <= col < 7:
        return True
    return False


def generate_qr_raster(config: QRConfig) -> Tuple[Image.Image, Image.Image]:
    """
    Generate high quality raster PIL Image of the QR code with custom colors,
    eye shapes, gradients, and embedded logo.
    Returns (rgba_image, display_ready_image).
    """
    ecc = ECC_MAP.get(config.error_correction, ERROR_CORRECT_H)
    qr = qrcode.QRCode(
        error_correction=ecc,
        box_size=config.box_size,
        border=config.border
    )
    qr.add_data(config.data)
    qr.make(fit=True)

    matrix = qr.modules
    grid_size = len(matrix)
    box_size = config.box_size
    border = config.border
    total_size = (grid_size + 2 * border) * box_size

    # Background
    bg_rgba = parse_color_rgba(config.colors.back_color)
    img = Image.new("RGBA", (total_size, total_size), bg_rgba)
    draw = ImageDraw.Draw(img)

    # Colors
    c_start = parse_color_rgb(config.colors.front_color)
    c_end = parse_color_rgb(config.colors.gradient_end_color or config.colors.front_color)
    eye_outer_rgb = parse_color_rgb(config.colors.eye_outer_color or config.colors.front_color)
    eye_inner_rgb = parse_color_rgb(config.colors.eye_inner_color or config.colors.front_color)

    eye_outer_rgba = (eye_outer_rgb[0], eye_outer_rgb[1], eye_outer_rgb[2], 255)
    eye_inner_rgba = (eye_inner_rgb[0], eye_inner_rgb[1], eye_inner_rgb[2], 255)

    # Draw body data modules (excluding finder patterns)
    for r in range(grid_size):
        for c in range(grid_size):
            if is_finder_module(r, c, grid_size):
                continue
            if matrix[r][c]:
                mod_color = get_module_color(
                    r, c, grid_size, total_size, box_size, border,
                    c_start, c_end, config.colors.gradient_type
                )
                x = (c + border) * box_size
                y = (r + border) * box_size

                if config.module_style == ModuleStyle.CIRCLE:
                    draw.ellipse([x + 1, y + 1, x + box_size - 2, y + box_size - 2], fill=mod_color)
                elif config.module_style == ModuleStyle.ROUNDED:
                    draw.rounded_rectangle(
                        [x + 1, y + 1, x + box_size - 2, y + box_size - 2],
                        radius=max(2, box_size // 3),
                        fill=mod_color
                    )
                elif config.module_style == ModuleStyle.GAPPED:
                    draw.rectangle([x + 2, y + 2, x + box_size - 3, y + box_size - 3], fill=mod_color)
                else:  # Square
                    draw.rectangle([x, y, x + box_size - 1, y + box_size - 1], fill=mod_color)

    # Draw the 3 finder eyes
    finder_positions = [
        (border, border),
        (border, border + grid_size - 7),
        (border + grid_size - 7, border)
    ]

    for ey_r, ey_c in finder_positions:
        ox = ey_c * box_size
        oy = ey_r * box_size
        ow = 7 * box_size

        if config.eye_style == EyeStyle.CIRCLE:
            # Outer circular ring
            draw.ellipse([ox, oy, ox + ow - 1, oy + ow - 1], fill=eye_outer_rgba)
            draw.ellipse([ox + box_size, oy + box_size, ox + ow - box_size - 1, oy + ow - box_size - 1], fill=bg_rgba)
            # Inner circle ball
            draw.ellipse([ox + 2 * box_size, oy + 2 * box_size, ox + 5 * box_size - 1, oy + 5 * box_size - 1], fill=eye_inner_rgba)
        elif config.eye_style == EyeStyle.ROUNDED:
            # Outer rounded frame
            draw.rounded_rectangle([ox, oy, ox + ow - 1, oy + ow - 1], radius=int(box_size * 1.5), fill=eye_outer_rgba)
            draw.rounded_rectangle(
                [ox + box_size, oy + box_size, ox + ow - box_size - 1, oy + ow - box_size - 1],
                radius=box_size,
                fill=bg_rgba
            )
            # Inner rounded ball
            draw.rounded_rectangle(
                [ox + 2 * box_size, oy + 2 * box_size, ox + 5 * box_size - 1, oy + 5 * box_size - 1],
                radius=max(2, box_size // 2),
                fill=eye_inner_rgba
            )
        else:  # Square
            # Outer square frame
            draw.rectangle([ox, oy, ox + ow - 1, oy + ow - 1], fill=eye_outer_rgba)
            draw.rectangle([ox + box_size, oy + box_size, ox + ow - box_size - 1, oy + ow - box_size - 1], fill=bg_rgba)
            # Inner square ball
            draw.rectangle([ox + 2 * box_size, oy + 2 * box_size, ox + 5 * box_size - 1, oy + 5 * box_size - 1], fill=eye_inner_rgba)

    # Embed Logo if configured
    if config.logo:
        raw_logo = load_logo_image(config.logo)
        if raw_logo:
            # Safe scale calculation: strictly clamped between 8% and 28% of QR size
            scale = max(0.08, min(0.28, config.logo.scale))
            logo_target_size = int(total_size * scale)
            processed_logo = mask_logo(raw_logo, config.logo.shape)
            processed_logo = processed_logo.resize((logo_target_size, logo_target_size), Image.Resampling.LANCZOS)

            pos_x = (total_size - logo_target_size) // 2
            pos_y = (total_size - logo_target_size) // 2
            pad = max(2, config.logo.padding)

            logo_bg_rgba = parse_color_rgba(config.logo.bg_color or "#ffffff")

            # Quiet zone pad behind the logo to prevent module bleeding
            if config.logo.shape == LogoShape.CIRCLE:
                draw.ellipse(
                    [pos_x - pad, pos_y - pad, pos_x + logo_target_size + pad - 1, pos_y + logo_target_size + pad - 1],
                    fill=logo_bg_rgba
                )
            elif config.logo.shape == LogoShape.ROUNDED:
                draw.rounded_rectangle(
                    [pos_x - pad, pos_y - pad, pos_x + logo_target_size + pad - 1, pos_y + logo_target_size + pad - 1],
                    radius=int(logo_target_size * 0.22) + pad,
                    fill=logo_bg_rgba
                )
            else:
                draw.rectangle(
                    [pos_x - pad, pos_y - pad, pos_x + logo_target_size + pad - 1, pos_y + logo_target_size + pad - 1],
                    fill=logo_bg_rgba
                )

            # Paste logo onto composite image
            img.paste(processed_logo, (pos_x, pos_y), mask=processed_logo)

    return img


def generate_qr_svg(config: QRConfig) -> str:
    """
    Generate scalable vector SVG markup for the QR code, supporting gradients,
    custom eye shapes, and embedded logo images.
    """
    ecc = ECC_MAP.get(config.error_correction, ERROR_CORRECT_H)
    qr = qrcode.QRCode(
        error_correction=ecc,
        box_size=config.box_size,
        border=config.border
    )
    qr.add_data(config.data)
    qr.make(fit=True)

    matrix = qr.modules
    grid_size = len(matrix)
    box_size = config.box_size
    border = config.border
    total_size = (grid_size + 2 * border) * box_size

    c_start_hex = config.colors.front_color
    c_end_hex = config.colors.gradient_end_color or config.colors.front_color
    bg_hex = config.colors.back_color
    eye_outer_hex = config.colors.eye_outer_color or config.colors.front_color
    eye_inner_hex = config.colors.eye_inner_color or config.colors.front_color

    svg_parts = []
    svg_parts.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
        f'viewBox="0 0 {total_size} {total_size}" width="{total_size}" height="{total_size}">'
    )

    # Defs for gradient
    defs = []
    fill_ref = c_start_hex
    grad_type = config.colors.gradient_type

    if grad_type != GradientType.NONE and c_start_hex != c_end_hex:
        fill_ref = "url(#qr-body-grad)"
        if grad_type == GradientType.LINEAR_HORIZONTAL:
            defs.append(
                f'<linearGradient id="qr-body-grad" x1="0%" y1="0%" x2="100%" y2="0%">'
                f'<stop offset="0%" stop-color="{c_start_hex}"/><stop offset="100%" stop-color="{c_end_hex}"/>'
                f'</linearGradient>'
            )
        elif grad_type == GradientType.LINEAR_VERTICAL:
            defs.append(
                f'<linearGradient id="qr-body-grad" x1="0%" y1="0%" x2="0%" y2="100%">'
                f'<stop offset="0%" stop-color="{c_start_hex}"/><stop offset="100%" stop-color="{c_end_hex}"/>'
                f'</linearGradient>'
            )
        elif grad_type == GradientType.LINEAR_DIAGONAL:
            defs.append(
                f'<linearGradient id="qr-body-grad" x1="0%" y1="0%" x2="100%" y2="100%">'
                f'<stop offset="0%" stop-color="{c_start_hex}"/><stop offset="100%" stop-color="{c_end_hex}"/>'
                f'</linearGradient>'
            )
        elif grad_type == GradientType.RADIAL:
            defs.append(
                f'<radialGradient id="qr-body-grad" cx="50%" cy="50%" r="50%" fx="50%" fy="50%">'
                f'<stop offset="0%" stop-color="{c_start_hex}"/><stop offset="100%" stop-color="{c_end_hex}"/>'
                f'</radialGradient>'
            )

    if defs:
        svg_parts.append('<defs>' + "".join(defs) + '</defs>')

    # Background
    if bg_hex.lower() not in ("transparent", "none"):
        svg_parts.append(f'<rect width="100%" height="100%" fill="{bg_hex}"/>')

    # Draw body modules
    body_elements = []
    for r in range(grid_size):
        for c in range(grid_size):
            if is_finder_module(r, c, grid_size):
                continue
            if matrix[r][c]:
                x = (c + border) * box_size
                y = (r + border) * box_size
                if config.module_style == ModuleStyle.CIRCLE:
                    cx = x + box_size / 2.0
                    cy = y + box_size / 2.0
                    rad = (box_size - 2) / 2.0
                    body_elements.append(f'<circle cx="{cx}" cy="{cy}" r="{rad}" fill="{fill_ref}"/>')
                elif config.module_style == ModuleStyle.ROUNDED:
                    radius = max(2, box_size // 3)
                    body_elements.append(
                        f'<rect x="{x + 1}" y="{y + 1}" width="{box_size - 2}" height="{box_size - 2}" '
                        f'rx="{radius}" ry="{radius}" fill="{fill_ref}"/>'
                    )
                elif config.module_style == ModuleStyle.GAPPED:
                    body_elements.append(
                        f'<rect x="{x + 2}" y="{y + 2}" width="{box_size - 4}" height="{box_size - 4}" fill="{fill_ref}"/>'
                    )
                else:  # Square
                    body_elements.append(
                        f'<rect x="{x}" y="{y}" width="{box_size}" height="{box_size}" fill="{fill_ref}"/>'
                    )

    svg_parts.append("".join(body_elements))

    # Finder Eyes
    finder_positions = [
        (border, border),
        (border, border + grid_size - 7),
        (border + grid_size - 7, border)
    ]

    bg_fill_str = bg_hex if bg_hex.lower() not in ("transparent", "none") else "transparent"

    for ey_r, ey_c in finder_positions:
        ox = ey_c * box_size
        oy = ey_r * box_size
        ow = 7 * box_size

        if config.eye_style == EyeStyle.CIRCLE:
            cx = ox + ow / 2.0
            cy = oy + ow / 2.0
            svg_parts.append(f'<circle cx="{cx}" cy="{cy}" r="{ow / 2.0}" fill="{eye_outer_hex}"/>')
            if bg_fill_str != "transparent":
                svg_parts.append(f'<circle cx="{cx}" cy="{cy}" r="{(5 * box_size) / 2.0}" fill="{bg_fill_str}"/>')
            else:
                # If transparent background, SVG mask can cut out
                svg_parts.append(f'<circle cx="{cx}" cy="{cy}" r="{(5 * box_size) / 2.0}" fill="#ffffff"/>')
            svg_parts.append(f'<circle cx="{cx}" cy="{cy}" r="{(3 * box_size) / 2.0}" fill="{eye_inner_hex}"/>')
        elif config.eye_style == EyeStyle.ROUNDED:
            rx = int(box_size * 1.5)
            svg_parts.append(f'<rect x="{ox}" y="{oy}" width="{ow}" height="{ow}" rx="{rx}" ry="{rx}" fill="{eye_outer_hex}"/>')
            svg_parts.append(
                f'<rect x="{ox + box_size}" y="{oy + box_size}" width="{5 * box_size}" height="{5 * box_size}" '
                f'rx="{box_size}" ry="{box_size}" fill="{bg_fill_str}"/>'
            )
            svg_parts.append(
                f'<rect x="{ox + 2 * box_size}" y="{oy + 2 * box_size}" width="{3 * box_size}" height="{3 * box_size}" '
                f'rx="{box_size // 2}" ry="{box_size // 2}" fill="{eye_inner_hex}"/>'
            )
        else:  # Square
            svg_parts.append(f'<rect x="{ox}" y="{oy}" width="{ow}" height="{ow}" fill="{eye_outer_hex}"/>')
            svg_parts.append(
                f'<rect x="{ox + box_size}" y="{oy + box_size}" width="{5 * box_size}" height="{5 * box_size}" '
                f'fill="{bg_fill_str}"/>'
            )
            svg_parts.append(
                f'<rect x="{ox + 2 * box_size}" y="{oy + 2 * box_size}" width="{3 * box_size}" height="{3 * box_size}" '
                f'fill="{eye_inner_hex}"/>'
            )

    # Embed Logo in SVG
    if config.logo:
        raw_logo = load_logo_image(config.logo)
        if raw_logo:
            scale = max(0.08, min(0.28, config.logo.scale))
            logo_target_size = int(total_size * scale)
            processed_logo = mask_logo(raw_logo, config.logo.shape)
            processed_logo = processed_logo.resize((logo_target_size, logo_target_size), Image.Resampling.LANCZOS)

            pos_x = (total_size - logo_target_size) // 2
            pos_y = (total_size - logo_target_size) // 2
            pad = max(2, config.logo.padding)
            logo_bg = config.logo.bg_color or "#ffffff"

            # Quiet zone pad
            if config.logo.shape == LogoShape.CIRCLE:
                cx = pos_x + logo_target_size / 2.0
                cy = pos_y + logo_target_size / 2.0
                svg_parts.append(f'<circle cx="{cx}" cy="{cy}" r="{logo_target_size / 2.0 + pad}" fill="{logo_bg}"/>')
            elif config.logo.shape == LogoShape.ROUNDED:
                rx = int(logo_target_size * 0.22) + pad
                svg_parts.append(
                    f'<rect x="{pos_x - pad}" y="{pos_y - pad}" width="{logo_target_size + 2 * pad}" '
                    f'height="{logo_target_size + 2 * pad}" rx="{rx}" ry="{rx}" fill="{logo_bg}"/>'
                )
            else:
                svg_parts.append(
                    f'<rect x="{pos_x - pad}" y="{pos_y - pad}" width="{logo_target_size + 2 * pad}" '
                    f'height="{logo_target_size + 2 * pad}" fill="{logo_bg}"/>'
                )

            # Convert processed logo to data URI
            buf = io.BytesIO()
            processed_logo.save(buf, format="PNG")
            logo_b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
            svg_parts.append(
                f'<image x="{pos_x}" y="{pos_y}" width="{logo_target_size}" height="{logo_target_size}" '
                f'xlink:href="data:image/png;base64,{logo_b64}"/>'
            )

    svg_parts.append('</svg>')
    return "".join(svg_parts)


def generate_qr(config: QRConfig) -> GenerationResult:
    """
    Main entrypoint to generate and validate a QR code.
    Produces either raster or vector output, and immediately executes
    automated scannability and link retention verification.
    """
    # Enforce safe ECC if logo is attached
    if config.logo and config.error_correction in (ErrorCorrection.L, ErrorCorrection.M):
        config.error_correction = ErrorCorrection.H

    raster_img = generate_qr_raster(config)
    w, h = raster_img.size

    # Automatic link retention & scannability verification
    validation = verify_qr_image(raster_img, config.data, config)

    image_b64 = None
    svg_content = None

    fmt = config.format.upper()
    if fmt == "SVG":
        svg_content = generate_qr_svg(config)
    else:
        # Encode raster to base64
        buf = io.BytesIO()
        if fmt == "JPEG" or fmt == "JPG":
            # Composite against white for JPEG
            bg = Image.new("RGB", raster_img.size, (255, 255, 255))
            bg.paste(raster_img, mask=raster_img.split()[3])
            bg.save(buf, format="JPEG", quality=95)
        elif fmt == "WEBP":
            raster_img.save(buf, format="WEBP", quality=95)
        else:  # PNG default
            raster_img.save(buf, format="PNG")
        image_b64 = f"data:image/{fmt.lower()};base64," + base64.b64encode(buf.getvalue()).decode("utf-8")

    return GenerationResult(
        image_base64=image_b64,
        svg_content=svg_content,
        format=fmt,
        width=w,
        height=h,
        validation=validation
    )
