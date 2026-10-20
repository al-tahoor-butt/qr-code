"""
Curated designer presets for QR Architect.
"""

from typing import Dict, Any
from qr_architect.models import ModuleStyle, EyeStyle, GradientType, ErrorCorrection


PRESETS: Dict[str, Dict[str, Any]] = {
    "modern_tech": {
        "name": "Modern Tech",
        "description": "Crisp slate body with indigo finder frame and cyan inner ball",
        "colors": {
            "front_color": "#1e293b",
            "back_color": "#ffffff",
            "gradient_type": GradientType.NONE,
            "eye_outer_color": "#4338ca",
            "eye_inner_color": "#06b6d4"
        },
        "module_style": ModuleStyle.ROUNDED,
        "eye_style": EyeStyle.ROUNDED,
        "error_correction": ErrorCorrection.H
    },
    "sunset_glow": {
        "name": "Sunset Glow",
        "description": "Smooth diagonal sunset gradient from coral rose to vibrant violet",
        "colors": {
            "front_color": "#e11d48",
            "back_color": "#ffffff",
            "gradient_type": GradientType.LINEAR_DIAGONAL,
            "gradient_end_color": "#7c3aed",
            "eye_outer_color": "#be123c",
            "eye_inner_color": "#6d28d9"
        },
        "module_style": ModuleStyle.ROUNDED,
        "eye_style": EyeStyle.ROUNDED,
        "error_correction": ErrorCorrection.H
    },
    "emerald_pro": {
        "name": "Emerald Pro",
        "description": "Executive emerald green theme with forest frame and mint accents",
        "colors": {
            "front_color": "#047857",
            "back_color": "#ffffff",
            "gradient_type": GradientType.NONE,
            "eye_outer_color": "#064e3b",
            "eye_inner_color": "#10b981"
        },
        "module_style": ModuleStyle.CIRCLE,
        "eye_style": EyeStyle.CIRCLE,
        "error_correction": ErrorCorrection.H
    },
    "cyberpunk_neon": {
        "name": "Cyberpunk Neon",
        "description": "Dark midnight background with glowing cyan data and magenta eye frames",
        "colors": {
            "front_color": "#06b6d4",
            "back_color": "#0b0f19",
            "gradient_type": GradientType.LINEAR_HORIZONTAL,
            "gradient_end_color": "#3b82f6",
            "eye_outer_color": "#ec4899",
            "eye_inner_color": "#06b6d4"
        },
        "module_style": ModuleStyle.ROUNDED,
        "eye_style": EyeStyle.ROUNDED,
        "error_correction": ErrorCorrection.H
    },
    "royal_violet": {
        "name": "Royal Violet",
        "description": "Rich purple to fuchsia horizontal gradient with matching eyes",
        "colors": {
            "front_color": "#6366f1",
            "back_color": "#f8fafc",
            "gradient_type": GradientType.LINEAR_HORIZONTAL,
            "gradient_end_color": "#d946ef",
            "eye_outer_color": "#4f46e5",
            "eye_inner_color": "#c026d3"
        },
        "module_style": ModuleStyle.ROUNDED,
        "eye_style": EyeStyle.ROUNDED,
        "error_correction": ErrorCorrection.H
    },
    "corporate_navy": {
        "name": "Corporate Navy",
        "description": "Authoritative deep navy blue with subtle rounded dots",
        "colors": {
            "front_color": "#1e3a8a",
            "back_color": "#ffffff",
            "gradient_type": GradientType.NONE,
            "eye_outer_color": "#1e3a8a",
            "eye_inner_color": "#2563eb"
        },
        "module_style": ModuleStyle.ROUNDED,
        "eye_style": EyeStyle.ROUNDED,
        "error_correction": ErrorCorrection.H
    },
    "minimal_monochrome": {
        "name": "Minimal Monochrome",
        "description": "Pure black-and-white high scannability design with circular eye frames",
        "colors": {
            "front_color": "#000000",
            "back_color": "#ffffff",
            "gradient_type": GradientType.NONE,
            "eye_outer_color": "#000000",
            "eye_inner_color": "#000000"
        },
        "module_style": ModuleStyle.SQUARE,
        "eye_style": EyeStyle.CIRCLE,
        "error_correction": ErrorCorrection.H
    }
}


def get_preset(name: str) -> Dict[str, Any]:
    """Retrieve preset by key."""
    return PRESETS.get(name, PRESETS["modern_tech"])
