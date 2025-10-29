"""Application settings and configuration management."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class DetectionConfig:
    """Configuration for PII detection methods."""

    # Method enable/disable states
    column_name_enabled: bool = True
    format_pattern_enabled: bool = True
    sparsity_enabled: bool = True
    ai_text_enabled: bool = True
    location_population_enabled: bool = False

    # Method-specific settings
    confidence_threshold: float = 0.7
    language: str = "en"
    sample_size: int = 100
    chunk_size: int = 1000
    max_workers: int = 4

    # Sparsity analysis settings
    sparsity_threshold: float = 0.6

    # Location population settings
    population_threshold: int = 15000

    # Text analysis settings
    text_analysis_mode: str = "comprehensive"  # quick, balanced, comprehensive


@dataclass
class FileInfo:
    """Information about a selected file."""

    path: Path
    name: str
    size_mb: float
    format: str
    is_valid: bool = True
    validation_message: str = ""


@dataclass
class ValidationResult:
    """Result of file validation."""

    is_valid: bool
    message: str
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class DetectionResult:
    """Result of PII detection for a single column."""

    column: str
    method: str
    confidence: float
    pii_type: str
    entity_types: list[str] = field(default_factory=list)
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class AppState:
    """Central application state management."""

    # Navigation state
    current_screen: str = "dashboard"
    screen_history: list[str] = field(default_factory=list)

    # File management
    selected_files: list[FileInfo] = field(default_factory=list)
    file_validation_results: dict[str, ValidationResult] = field(default_factory=dict)

    # Configuration state
    detection_config: DetectionConfig = field(default_factory=DetectionConfig)
    preset_mode: str = "balanced"  # quick, balanced, thorough

    # Processing state
    is_processing: bool = False
    current_progress: float = 0.0
    processing_stage: str = ""
    estimated_time_remaining: int | None = None
    current_file: str = ""

    # Results state
    detection_results: list[DetectionResult] = field(default_factory=list)
    user_actions: dict[str, str] = field(
        default_factory=dict
    )  # column -> action mapping

    # Anonymization configuration - per-column methods
    column_anonymization_methods: dict[str, str] = field(
        default_factory=dict
    )  # column_name -> method (remove, encode, categorize, mask)

    # UI state
    panel_expansion_states: dict[str, bool] = field(default_factory=dict)
    error_messages: list[str] = field(default_factory=list)
    success_messages: list[str] = field(default_factory=list)

    # API keys and external service configuration
    geonames_api_key: str | None = None


class AppSettings:
    """Application settings and preferences."""

    def __init__(self):
        """Initialize application settings with default values."""
        self.window_width = 1200
        self.window_height = 800
        self.theme_mode = "light"
        self.default_export_path = Path.home() / "Downloads"
        self.remember_settings = True

    def save_settings(self):
        """Save settings to file (implementation depends on requirements)."""
        pass

    def load_settings(self):
        """Load settings from file (implementation depends on requirements)."""
        pass
