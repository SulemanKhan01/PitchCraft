"""
constants.py — AB {Ark} Brand Design System Tokens

Centralized design system constants including exact RGB/HEX brand colors, font families,
font sizes, table dimensions, and layout measurements matching AB Ark's brand identity.
"""

from docx.shared import Inches, Pt, RGBColor

# ---------------- BRAND COLORS ---------------- #
# Primary Mid-Blue (Cover project title, H1 headers, lines, hyperlinks)
HEX_PRIMARY_BLUE = "1F6FBF"
RGB_PRIMARY_BLUE = RGBColor(31, 111, 191)

# Dark Navy / Black (Phase banners, dark table headers)
HEX_NAVY = "0F172A"
RGB_NAVY = RGBColor(15, 23, 42)

# Accent Orange (Phase banner sub-labels, investment highlight numbers)
HEX_ORANGE = "E65100"
RGB_ORANGE = RGBColor(230, 81, 0)

# Neutral Dark (Body text, subheadings)
HEX_TEXT_BLACK = "1E293B"
RGB_TEXT_BLACK = RGBColor(30, 41, 59)

# Muted Gray (Secondary text, metadata, copyright notice)
HEX_TEXT_MUTED = "64748B"
RGB_TEXT_MUTED = RGBColor(100, 116, 139)

# Table Alternating Row Shading & Borders
HEX_BG_LIGHT_GRAY = "F8FAFC"
HEX_WHITE = "FFFFFF"
RGB_WHITE = RGBColor(255, 255, 255)
HEX_BORDER_GRAY = "E2E8F0"

# ---------------- TYPOGRAPHY ---------------- #
FONT_PRIMARY = "Arial"

# Font Sizes (pt)
SIZE_COVER_TITLE = Pt(26)
SIZE_COVER_SUBTITLE = Pt(15)
SIZE_COVER_FROM = Pt(13)
SIZE_H1 = Pt(17)
SIZE_H2 = Pt(13)
SIZE_BODY = Pt(10.5)
SIZE_HEADER_FOOTER = Pt(8.5)
SIZE_BANNER_LABEL = Pt(9)
SIZE_BANNER_TITLE = Pt(14)
SIZE_BANNER_VALUE = Pt(12)

# ---------------- LAYOUT MEASUREMENTS ---------------- #
MARGIN_TOP = Inches(0.8)
MARGIN_BOTTOM = Inches(0.8)
MARGIN_LEFT = Inches(0.8)
MARGIN_RIGHT = Inches(0.8)

HEADER_LOGO_WIDTH = Inches(0.9)
COVER_CENTER_LOGO_WIDTH = Inches(3.0)

# ---------------- DEFAULT STATIC CONTENT ---------------- #
DEFAULT_DISCLAIMER = (
    "This proposal contains confidential and proprietary information belonging to AB {Ark}. "
    "It is provided solely for evaluation purposes by the intended client."
)
DEFAULT_FOOTER_COPYRIGHT = "All copyrights are reserved with AB Ark"
DEFAULT_FOOTER_CONTACT = "www.abark.tech | contact@abark.pk | +92 328 8028640"
