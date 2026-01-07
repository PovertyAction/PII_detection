"""Constants for the PII Detector Flet application.

This module contains all color, typography, and spacing constants
following the IPA design system specifications.
"""


class IPAColors:
    """IPA brand color palette."""

    # Primary Brand Colors
    IPA_GREEN = "#49ac57"  # Primary actions, success states
    DARK_GREEN = "#155240"  # Sequential data, deep success
    LIGHT_BLUE = "#84d0d4"  # Secondary actions, hover states
    DARK_BLUE = "#2b4085"  # Headers, navigation, primary text
    RED_ORANGE = "#f26529"  # High-confidence alerts, critical actions

    # Neutral Palette
    LIGHT_GREY = "#f1f2f2"  # Background, card surfaces
    DARK_GREY = "#c9c9c8"  # Borders, secondary text
    CHARCOAL = "#414042"  # Primary text, icons
    BLUE_ACCENT = "#ceecee"  # Subtle highlights, table alternation

    # Confidence Level Indicators
    HIGH_CONFIDENCE = RED_ORANGE  # 0.8+ confidence scores
    MED_CONFIDENCE = "#f5cb57"  # 0.5-0.8 confidence scores
    LOW_CONFIDENCE = DARK_GREY  # <0.5 confidence scores

    # Interactive States
    HOVER_COLOR = BLUE_ACCENT
    ACTIVE_COLOR = IPA_GREEN
    DISABLED_COLOR = DARK_GREY

    # Additional semantic colors
    WHITE = "#ffffff"
    SUCCESS = IPA_GREEN
    WARNING = MED_CONFIDENCE
    ERROR = RED_ORANGE
    INFO = LIGHT_BLUE


class IPATypography:
    """Typography system for consistent text styling."""

    # Font families (system fonts with fallbacks)
    PRIMARY_FONT = "Segoe UI, -apple-system, BlinkMacSystemFont, sans-serif"
    MONOSPACE_FONT = "Consolas, Monaco, Courier New, monospace"

    # Font sizes (in pixels for Flet)
    HEADER_1 = 32  # Main page titles
    HEADER_2 = 24  # Section headers
    HEADER_3 = 18  # Subsection titles
    BODY_LARGE = 16  # Primary text, buttons
    BODY_REGULAR = 14  # Secondary text, labels
    BODY_SMALL = 12  # Captions, metadata
    CODE_TEXT = 12  # Monospace content

    # Font weights (Flet FontWeight enum values)
    LIGHT = "w300"
    REGULAR = "w400"
    MEDIUM = "w500"
    SEMIBOLD = "w600"
    BOLD = "w700"


class IPASpacing:
    """Spacing system based on 8px grid."""

    # Base spacing unit (8px grid system)
    UNIT = 8

    # Common spacing values
    XS = UNIT // 2  # 4px - tight spacing
    SM = UNIT  # 8px - compact spacing
    MD = UNIT * 2  # 16px - standard spacing
    LG = UNIT * 3  # 24px - generous spacing
    XL = UNIT * 4  # 32px - section spacing
    XXL = UNIT * 6  # 48px - major section breaks

    # Component-specific spacing
    CARD_PADDING = MD
    BUTTON_PADDING_H = MD
    BUTTON_PADDING_V = SM
    INPUT_PADDING = SM

    # Border radius values
    RADIUS_SM = 4  # Small elements (checkboxes, small buttons)
    RADIUS_MD = 8  # Cards, input fields
    RADIUS_LG = 12  # Major containers, panels


class AppConstants:
    """Application-specific constants."""

    # File size limits
    MAX_FILE_SIZE_MB = 100

    # Supported file formats
    SUPPORTED_FORMATS = [".csv", ".xlsx", ".xls", ".dta"]

    # Screen names
    SCREEN_DASHBOARD = "dashboard"
    SCREEN_FILE_SELECTION = "file_selection"
    SCREEN_CONFIGURATION = "configuration"
    SCREEN_PROGRESS = "progress"
    SCREEN_RESULTS = "results"
    SCREEN_SETTINGS = "settings"

    # Detection method names
    METHOD_COLUMN_NAME = "Column Name Analysis"
    METHOD_FORMAT_PATTERN = "Format Pattern Detection"
    METHOD_SPARSITY = "Sparsity Analysis"
    METHOD_AI_TEXT = "AI Text Analysis (Presidio)"
    METHOD_LOCATION_POPULATION = "Location Population Check"
