"""
Enterprise Design System tokens for MEMMS:
Color palettes, typography scale, spacing tokens, and border radii.
"""
from dataclasses import dataclass

# Spacing Tokens
SPACING_XS = 4
SPACING_SM = 8
SPACING_MD = 16
SPACING_LG = 24
SPACING_XL = 32

# Typography Scale
FONT_SIZE_XS = 11
FONT_SIZE_SM = 12
FONT_SIZE_BASE = 13
FONT_SIZE_MD = 15
FONT_SIZE_LG = 18
FONT_SIZE_XL = 22
FONT_SIZE_2XL = 26

FONT_FAMILY = "'Segoe UI', 'Cairo', 'Tajawal', 'Inter', -apple-system, BlinkMacSystemFont, sans-serif"


@dataclass(frozen=True)
class ColorPalette:
    # Brand Identity (Medical Teal / Slate)
    PRIMARY: str
    PRIMARY_HOVER: str
    PRIMARY_ACTIVE: str
    PRIMARY_LIGHT: str

    SECONDARY: str
    SECONDARY_HOVER: str
    SECONDARY_LIGHT: str

    # State & Feedback Colors
    SUCCESS: str
    SUCCESS_BG: str
    SUCCESS_BORDER: str

    WARNING: str
    WARNING_BG: str
    WARNING_BORDER: str

    DANGER: str
    DANGER_BG: str
    DANGER_BORDER: str

    INFO: str
    INFO_BG: str
    INFO_BORDER: str

    # Backgrounds & Surfaces
    BG_MAIN: str
    BG_SURFACE: str
    BG_SURFACE_HOVER: str
    BG_SIDEBAR: str
    BG_SIDEBAR_HOVER: str
    BG_SIDEBAR_ACTIVE: str
    BG_HEADER: str
    BG_INPUT: str
    BG_STATUS_BAR: str

    # Borders & Dividers
    BORDER: str
    BORDER_LIGHT: str
    BORDER_FOCUS: str
    BORDER_SIDEBAR: str

    # Typography
    TEXT_PRIMARY: str
    TEXT_SECONDARY: str
    TEXT_MUTED: str
    TEXT_INVERTED: str
    TEXT_SIDEBAR: str
    TEXT_SIDEBAR_ACTIVE: str


LIGHT_PALETTE = ColorPalette(
    PRIMARY="#0F766E",          # Deep Medical Teal
    PRIMARY_HOVER="#0D9488",
    PRIMARY_ACTIVE="#115E59",
    PRIMARY_LIGHT="#CCFBF1",

    SECONDARY="#334155",        # Slate
    SECONDARY_HOVER="#1E293B",
    SECONDARY_LIGHT="#F1F5F9",

    SUCCESS="#059669",          # Emerald
    SUCCESS_BG="#ECFDF5",
    SUCCESS_BORDER="#A7F3D0",

    WARNING="#D97706",          # Amber
    WARNING_BG="#FFFBEB",
    WARNING_BORDER="#FDE68A",

    DANGER="#DC2626",           # Crimson
    DANGER_BG="#FEF2F2",
    DANGER_BORDER="#FECACA",

    INFO="#0284C7",             # Sky Blue
    INFO_BG="#F0F9FF",
    INFO_BORDER="#BAE6FD",

    BG_MAIN="#F8FAFC",          # Ultra-clean slate background
    BG_SURFACE="#FFFFFF",       # Pure white cards
    BG_SURFACE_HOVER="#F1F5F9",
    BG_SIDEBAR="#0F172A",       # Enterprise Dark Navy
    BG_SIDEBAR_HOVER="#1E293B",
    BG_SIDEBAR_ACTIVE="#0F766E",
    BG_HEADER="#FFFFFF",
    BG_INPUT="#FFFFFF",
    BG_STATUS_BAR="#F1F5F9",

    BORDER="#E2E8F0",
    BORDER_LIGHT="#F1F5F9",
    BORDER_FOCUS="#0F766E",
    BORDER_SIDEBAR="#1E293B",

    TEXT_PRIMARY="#0F172A",     # High-contrast readable dark
    TEXT_SECONDARY="#475569",
    TEXT_MUTED="#94A3B8",
    TEXT_INVERTED="#FFFFFF",
    TEXT_SIDEBAR="#94A3B8",
    TEXT_SIDEBAR_ACTIVE="#FFFFFF"
)

# Active single palette
THEME_PALETTE = LIGHT_PALETTE
