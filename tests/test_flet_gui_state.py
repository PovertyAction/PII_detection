"""Integration tests for Flet GUI state management."""

from pathlib import Path
from unittest.mock import Mock

import pytest

from pii_detector.gui.flet_app.config.settings import (
    AppState,
    DetectionConfig,
    DetectionResult,
    FileInfo,
    ValidationResult,
)
from pii_detector.gui.flet_app.ui.app import StateManager


class TestAppState:
    """Test suite for AppState dataclass."""

    def test_app_state_initialization(self):
        """Test that AppState initializes with correct defaults."""
        state = AppState()

        # Navigation state
        assert state.current_screen == "dashboard"
        assert state.screen_history == []

        # File management
        assert state.selected_files == []
        assert state.file_validation_results == {}

        # Configuration state
        assert isinstance(state.detection_config, DetectionConfig)
        assert state.preset_mode == "balanced"

        # Processing state
        assert state.is_processing is False
        assert state.current_progress == 0.0
        assert state.processing_stage == ""
        assert state.estimated_time_remaining is None
        assert state.current_file == ""

        # Results state
        assert state.detection_results == []
        assert state.user_actions == {}
        assert state.column_anonymization_methods == {}

        # UI state
        assert state.panel_expansion_states == {}
        assert state.error_messages == []
        assert state.success_messages == []

        # API configuration
        assert state.geonames_api_key is None

    def test_app_state_file_selection(self):
        """Test file selection state management."""
        state = AppState()

        # Add a file
        file_info = FileInfo(
            path=Path("test.csv"),
            name="test.csv",
            size_mb=1.5,
            format="csv",
            is_valid=True,
            validation_message="",
        )
        state.selected_files.append(file_info)

        assert len(state.selected_files) == 1
        assert state.selected_files[0].name == "test.csv"
        assert state.selected_files[0].format == "csv"

    def test_app_state_detection_results(self):
        """Test detection results state management."""
        state = AppState()

        # Add detection results
        result = DetectionResult(
            column="email",
            method="format_pattern",
            confidence=0.95,
            pii_type="EMAIL_ADDRESS",
            entity_types=["EMAIL"],
            details={
                "pattern_matched": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
            },
        )
        state.detection_results.append(result)

        assert len(state.detection_results) == 1
        assert state.detection_results[0].column == "email"
        assert state.detection_results[0].confidence == 0.95

    def test_app_state_user_actions(self):
        """Test user action tracking."""
        state = AppState()

        # Set user actions for columns
        state.user_actions["email"] = "remove"
        state.user_actions["phone"] = "encode"
        state.user_actions["age"] = "categorize"

        assert state.user_actions["email"] == "remove"
        assert state.user_actions["phone"] == "encode"
        assert state.user_actions["age"] == "categorize"


class TestDetectionConfig:
    """Test suite for DetectionConfig dataclass."""

    def test_detection_config_defaults(self):
        """Test that DetectionConfig initializes with correct defaults."""
        config = DetectionConfig()

        # Method enable/disable states
        assert config.column_name_enabled is True
        assert config.format_pattern_enabled is True
        assert config.sparsity_enabled is True
        assert config.ai_text_enabled is True
        assert config.location_population_enabled is False

        # Column Name Detection settings
        assert config.fuzzy_match_threshold == 0.8
        assert config.matching_type == "fuzzy"

        # Format Pattern Detection settings
        assert config.format_confidence_threshold == 0.7
        assert config.detect_phone is True
        assert config.detect_email is True
        assert config.detect_ssn is True
        assert config.detect_dates is True

        # Sparsity analysis settings
        assert config.sparsity_threshold == 0.8
        assert config.min_entries_required == 10

        # Location population settings
        assert config.population_threshold == 50000

        # Presidio settings
        assert config.presidio_confidence_threshold == 0.8
        assert config.presidio_language_model == "en_core_web_sm"
        assert config.presidio_detect_person is True
        assert config.presidio_detect_org is True

    def test_detection_config_custom_values(self):
        """Test DetectionConfig with custom values."""
        config = DetectionConfig(
            column_name_enabled=False,
            fuzzy_match_threshold=0.9,
            matching_type="strict",
            format_confidence_threshold=0.85,
            detect_phone=False,
            sparsity_threshold=0.7,
            population_threshold=100000,
            presidio_confidence_threshold=0.75,
        )

        assert config.column_name_enabled is False
        assert config.fuzzy_match_threshold == 0.9
        assert config.matching_type == "strict"
        assert config.format_confidence_threshold == 0.85
        assert config.detect_phone is False
        assert config.sparsity_threshold == 0.7
        assert config.population_threshold == 100000
        assert config.presidio_confidence_threshold == 0.75

    def test_detection_config_validation_ranges(self):
        """Test that config values are within expected ranges."""
        config = DetectionConfig()

        # Threshold values should be between 0 and 1
        assert 0.0 <= config.fuzzy_match_threshold <= 1.0
        assert 0.0 <= config.format_confidence_threshold <= 1.0
        assert 0.0 <= config.sparsity_threshold <= 1.0
        assert 0.0 <= config.presidio_confidence_threshold <= 1.0

        # Population threshold should be positive
        assert config.population_threshold > 0

        # Min entries should be positive
        assert config.min_entries_required > 0


class TestStateManager:
    """Test suite for StateManager class."""

    @pytest.fixture
    def mock_page(self):
        """Create a mock Flet page."""
        page = Mock()
        page.update = Mock()
        return page

    @pytest.fixture
    def state_manager(self, mock_page):
        """Create a StateManager instance for testing."""
        return StateManager(mock_page)

    def test_state_manager_initialization(self, state_manager):
        """Test StateManager initialization."""
        assert isinstance(state_manager.state, AppState)
        assert state_manager.state.current_screen == "dashboard"

    def test_state_manager_update_state(self, state_manager):
        """Test state update functionality."""
        # Update detection config
        new_config = DetectionConfig(
            fuzzy_match_threshold=0.95,
            format_confidence_threshold=0.8,
        )
        state_manager.update_state(detection_config=new_config)

        assert state_manager.state.detection_config.fuzzy_match_threshold == 0.95
        assert state_manager.state.detection_config.format_confidence_threshold == 0.8

    def test_state_manager_navigation(self, state_manager):
        """Test navigation state management."""
        # Navigate to file selection
        state_manager.navigate_to("file_selection")
        assert state_manager.state.current_screen == "file_selection"
        assert "dashboard" in state_manager.state.screen_history

        # Navigate to configuration
        state_manager.navigate_to("configuration")
        assert state_manager.state.current_screen == "configuration"
        assert "file_selection" in state_manager.state.screen_history

    def test_state_manager_go_back(self, state_manager):
        """Test navigation back functionality."""
        # Navigate through screens
        state_manager.navigate_to("file_selection")
        state_manager.navigate_to("configuration")
        state_manager.navigate_to("progress")

        # Go back
        state_manager.go_back()
        assert state_manager.state.current_screen == "configuration"

        state_manager.go_back()
        assert state_manager.state.current_screen == "file_selection"

    def test_state_manager_add_file(self, state_manager):
        """Test adding files to state."""
        file_info = FileInfo(
            path=Path("test.csv"),
            name="test.csv",
            size_mb=2.0,
            format="csv",
            is_valid=True,
        )

        state_manager.add_file(file_info)
        assert len(state_manager.state.selected_files) == 1
        assert state_manager.state.selected_files[0].name == "test.csv"

    def test_state_manager_remove_file(self, state_manager):
        """Test removing files from state."""
        # Add files
        file1 = FileInfo(
            path=Path("test1.csv"),
            name="test1.csv",
            size_mb=1.0,
            format="csv",
        )
        file2 = FileInfo(
            path=Path("test2.csv"),
            name="test2.csv",
            size_mb=1.5,
            format="csv",
        )

        state_manager.add_file(file1)
        state_manager.add_file(file2)
        assert len(state_manager.state.selected_files) == 2

        # Remove first file
        state_manager.remove_file(Path("test1.csv"))
        assert len(state_manager.state.selected_files) == 1
        assert state_manager.state.selected_files[0].name == "test2.csv"

    def test_state_manager_clear_files(self, state_manager):
        """Test clearing all files from state."""
        # Add files
        file1 = FileInfo(
            path=Path("test1.csv"), name="test1.csv", size_mb=1.0, format="csv"
        )
        file2 = FileInfo(
            path=Path("test2.csv"), name="test2.csv", size_mb=1.5, format="csv"
        )

        state_manager.add_file(file1)
        state_manager.add_file(file2)

        # Clear files
        state_manager.clear_files()
        assert len(state_manager.state.selected_files) == 0

    def test_state_manager_add_detection_result(self, state_manager):
        """Test adding detection results to state."""
        result = DetectionResult(
            column="name",
            method="column_name",
            confidence=0.9,
            pii_type="PERSON",
            entity_types=["PERSON"],
        )

        state_manager.add_detection_result(result)
        assert len(state_manager.state.detection_results) == 1
        assert state_manager.state.detection_results[0].column == "name"

    def test_state_manager_set_user_action(self, state_manager):
        """Test setting user actions for columns."""
        state_manager.set_user_action("email", "remove")
        state_manager.set_user_action("phone", "encode")

        assert state_manager.state.user_actions["email"] == "remove"
        assert state_manager.state.user_actions["phone"] == "encode"

    def test_state_manager_add_error_message(self, state_manager):
        """Test adding error messages."""
        state_manager.add_error_message("Test error message")

        assert len(state_manager.state.error_messages) == 1
        assert state_manager.state.error_messages[0] == "Test error message"

    def test_state_manager_add_success_message(self, state_manager):
        """Test adding success messages."""
        state_manager.add_success_message("Test success message")

        assert len(state_manager.state.success_messages) == 1
        assert state_manager.state.success_messages[0] == "Test success message"

    def test_state_manager_clear_messages(self, state_manager):
        """Test clearing all messages."""
        state_manager.add_error_message("Error 1")
        state_manager.add_error_message("Error 2")
        state_manager.add_success_message("Success 1")

        state_manager.clear_messages()

        assert len(state_manager.state.error_messages) == 0
        assert len(state_manager.state.success_messages) == 0

    def test_state_manager_update_progress(self, state_manager):
        """Test updating processing progress."""
        state_manager.update_progress(
            progress=0.5,
            stage="Analyzing columns",
            current_file="test.csv",
            estimated_time_remaining=120,
        )

        assert state_manager.state.current_progress == 0.5
        assert state_manager.state.processing_stage == "Analyzing columns"
        assert state_manager.state.current_file == "test.csv"
        assert state_manager.state.estimated_time_remaining == 120

    def test_state_manager_set_processing(self, state_manager):
        """Test setting processing state."""
        state_manager.set_processing(True)
        assert state_manager.state.is_processing is True

        state_manager.set_processing(False)
        assert state_manager.state.is_processing is False

    def test_state_manager_set_api_key(self, state_manager):
        """Test setting API key."""
        state_manager.set_api_key("test_api_key_123")
        assert state_manager.state.geonames_api_key == "test_api_key_123"

    def test_state_manager_reset_state(self, state_manager):
        """Test resetting state to defaults."""
        # Modify state
        state_manager.navigate_to("configuration")
        state_manager.add_error_message("Error")
        state_manager.set_processing(True)

        # Reset
        state_manager.reset_state()

        # Verify reset
        assert state_manager.state.current_screen == "dashboard"
        assert len(state_manager.state.error_messages) == 0
        assert state_manager.state.is_processing is False


class TestFileInfo:
    """Test suite for FileInfo dataclass."""

    def test_file_info_creation(self):
        """Test FileInfo creation."""
        file_info = FileInfo(
            path=Path("test.csv"),
            name="test.csv",
            size_mb=2.5,
            format="csv",
            is_valid=True,
            validation_message="File is valid",
        )

        assert file_info.path == Path("test.csv")
        assert file_info.name == "test.csv"
        assert file_info.size_mb == 2.5
        assert file_info.format == "csv"
        assert file_info.is_valid is True
        assert file_info.validation_message == "File is valid"

    def test_file_info_invalid_file(self):
        """Test FileInfo for invalid file."""
        file_info = FileInfo(
            path=Path("invalid.txt"),
            name="invalid.txt",
            size_mb=0.1,
            format="txt",
            is_valid=False,
            validation_message="Unsupported file format",
        )

        assert file_info.is_valid is False
        assert file_info.validation_message == "Unsupported file format"


class TestValidationResult:
    """Test suite for ValidationResult dataclass."""

    def test_validation_result_valid(self):
        """Test ValidationResult for valid file."""
        result = ValidationResult(
            is_valid=True,
            message="File is valid",
            details={"rows": 100, "columns": 5},
        )

        assert result.is_valid is True
        assert result.message == "File is valid"
        assert result.details["rows"] == 100
        assert result.details["columns"] == 5

    def test_validation_result_invalid(self):
        """Test ValidationResult for invalid file."""
        result = ValidationResult(
            is_valid=False,
            message="File too large",
            details={"size_mb": 500, "max_size_mb": 100},
        )

        assert result.is_valid is False
        assert result.message == "File too large"
        assert result.details["size_mb"] == 500


class TestDetectionResult:
    """Test suite for DetectionResult dataclass."""

    def test_detection_result_creation(self):
        """Test DetectionResult creation."""
        result = DetectionResult(
            column="email",
            method="format_pattern",
            confidence=0.95,
            pii_type="EMAIL_ADDRESS",
            entity_types=["EMAIL"],
            details={"pattern": r".*@.*\..*"},
        )

        assert result.column == "email"
        assert result.method == "format_pattern"
        assert result.confidence == 0.95
        assert result.pii_type == "EMAIL_ADDRESS"
        assert result.entity_types == ["EMAIL"]
        assert "pattern" in result.details

    def test_detection_result_multiple_entity_types(self):
        """Test DetectionResult with multiple entity types."""
        result = DetectionResult(
            column="contact_info",
            method="presidio",
            confidence=0.85,
            pii_type="MIXED",
            entity_types=["PERSON", "EMAIL_ADDRESS", "PHONE_NUMBER"],
            details={
                "entities_found": {
                    "PERSON": 2,
                    "EMAIL_ADDRESS": 1,
                    "PHONE_NUMBER": 1,
                }
            },
        )

        assert len(result.entity_types) == 3
        assert "PERSON" in result.entity_types
        assert "EMAIL_ADDRESS" in result.entity_types
        assert "PHONE_NUMBER" in result.entity_types
