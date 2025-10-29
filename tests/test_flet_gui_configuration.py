"""Integration tests for Flet GUI configuration screen."""

from unittest.mock import Mock

import pytest

from pii_detector.gui.flet_app.config.settings import DetectionConfig
from pii_detector.gui.flet_app.ui.app import StateManager


class TestConfigurationScreen:
    """Test suite for configuration screen functionality."""

    @pytest.fixture
    def mock_page(self):
        """Create a mock Flet page."""
        page = Mock()
        page.update = Mock()
        page.open = Mock()
        return page

    @pytest.fixture
    def state_manager(self, mock_page):
        """Create a StateManager instance."""
        return StateManager(mock_page)

    @pytest.fixture
    def configuration_screen(self, mock_page, state_manager):
        """Create a ConfigurationScreen instance."""
        # We can't directly import due to Flet dependency, so we'll test through state
        return {
            "page": mock_page,
            "state_manager": state_manager,
        }

    def test_preset_quick_configuration(self, state_manager):
        """Test quick preset configuration values."""
        # Quick preset should enable only column name and format pattern detection
        config = DetectionConfig(
            column_name_enabled=True,
            format_pattern_enabled=True,
            sparsity_enabled=False,
            location_population_enabled=False,
            ai_text_enabled=False,
        )

        state_manager.update_state(detection_config=config, preset_mode="quick")

        assert state_manager.state.detection_config.column_name_enabled is True
        assert state_manager.state.detection_config.format_pattern_enabled is True
        assert state_manager.state.detection_config.sparsity_enabled is False
        assert state_manager.state.preset_mode == "quick"

    def test_preset_balanced_configuration(self, state_manager):
        """Test balanced preset configuration values."""
        # Balanced preset should enable most methods except location
        config = DetectionConfig(
            column_name_enabled=True,
            format_pattern_enabled=True,
            sparsity_enabled=True,
            location_population_enabled=False,
            ai_text_enabled=True,
        )

        state_manager.update_state(detection_config=config, preset_mode="balanced")

        assert state_manager.state.detection_config.column_name_enabled is True
        assert state_manager.state.detection_config.format_pattern_enabled is True
        assert state_manager.state.detection_config.sparsity_enabled is True
        assert state_manager.state.detection_config.ai_text_enabled is True
        assert state_manager.state.preset_mode == "balanced"

    def test_preset_thorough_configuration(self, state_manager):
        """Test thorough preset configuration values."""
        # Thorough preset should enable all methods
        config = DetectionConfig(
            column_name_enabled=True,
            format_pattern_enabled=True,
            sparsity_enabled=True,
            location_population_enabled=True,
            ai_text_enabled=True,
        )

        state_manager.update_state(detection_config=config, preset_mode="thorough")

        assert state_manager.state.detection_config.column_name_enabled is True
        assert state_manager.state.detection_config.format_pattern_enabled is True
        assert state_manager.state.detection_config.sparsity_enabled is True
        assert state_manager.state.detection_config.location_population_enabled is True
        assert state_manager.state.detection_config.ai_text_enabled is True
        assert state_manager.state.preset_mode == "thorough"

    def test_column_name_detection_settings(self, state_manager):
        """Test column name detection configuration."""
        config = DetectionConfig(
            column_name_enabled=True,
            fuzzy_match_threshold=0.9,
            matching_type="fuzzy",
        )

        state_manager.update_state(detection_config=config)

        assert state_manager.state.detection_config.column_name_enabled is True
        assert state_manager.state.detection_config.fuzzy_match_threshold == 0.9
        assert state_manager.state.detection_config.matching_type == "fuzzy"

    def test_column_name_strict_matching(self, state_manager):
        """Test strict matching configuration."""
        config = DetectionConfig(
            column_name_enabled=True,
            matching_type="strict",
        )

        state_manager.update_state(detection_config=config)

        assert state_manager.state.detection_config.matching_type == "strict"

    def test_column_name_both_matching(self, state_manager):
        """Test both (strict + fuzzy) matching configuration."""
        config = DetectionConfig(
            column_name_enabled=True,
            matching_type="both",
            fuzzy_match_threshold=0.85,
        )

        state_manager.update_state(detection_config=config)

        assert state_manager.state.detection_config.matching_type == "both"
        assert state_manager.state.detection_config.fuzzy_match_threshold == 0.85

    def test_format_pattern_detection_settings(self, state_manager):
        """Test format pattern detection configuration."""
        config = DetectionConfig(
            format_pattern_enabled=True,
            format_confidence_threshold=0.85,
            detect_phone=True,
            detect_email=True,
            detect_ssn=False,
            detect_dates=True,
        )

        state_manager.update_state(detection_config=config)

        assert state_manager.state.detection_config.format_pattern_enabled is True
        assert state_manager.state.detection_config.format_confidence_threshold == 0.85
        assert state_manager.state.detection_config.detect_phone is True
        assert state_manager.state.detection_config.detect_email is True
        assert state_manager.state.detection_config.detect_ssn is False
        assert state_manager.state.detection_config.detect_dates is True

    def test_sparsity_analysis_settings(self, state_manager):
        """Test sparsity analysis configuration."""
        config = DetectionConfig(
            sparsity_enabled=True,
            sparsity_threshold=0.75,
            min_entries_required=15,
        )

        state_manager.update_state(detection_config=config)

        assert state_manager.state.detection_config.sparsity_enabled is True
        assert state_manager.state.detection_config.sparsity_threshold == 0.75
        assert state_manager.state.detection_config.min_entries_required == 15

    def test_location_population_settings(self, state_manager):
        """Test location population detection configuration."""
        config = DetectionConfig(
            location_population_enabled=True,
            population_threshold=75000,
        )

        state_manager.update_state(detection_config=config)

        assert state_manager.state.detection_config.location_population_enabled is True
        assert state_manager.state.detection_config.population_threshold == 75000

    def test_presidio_ai_settings(self, state_manager):
        """Test Presidio AI text detection configuration."""
        config = DetectionConfig(
            ai_text_enabled=True,
            presidio_confidence_threshold=0.75,
            presidio_language_model="en_core_web_md",
            presidio_detect_person=True,
            presidio_detect_org=False,
        )

        state_manager.update_state(detection_config=config)

        assert state_manager.state.detection_config.ai_text_enabled is True
        assert (
            state_manager.state.detection_config.presidio_confidence_threshold == 0.75
        )
        assert (
            state_manager.state.detection_config.presidio_language_model
            == "en_core_web_md"
        )
        assert state_manager.state.detection_config.presidio_detect_person is True
        assert state_manager.state.detection_config.presidio_detect_org is False

    def test_threshold_value_ranges(self, state_manager):
        """Test that threshold values are within valid ranges."""
        # Test minimum values
        config_min = DetectionConfig(
            fuzzy_match_threshold=0.5,
            format_confidence_threshold=0.5,
            sparsity_threshold=0.5,
            presidio_confidence_threshold=0.5,
        )

        state_manager.update_state(detection_config=config_min)

        assert state_manager.state.detection_config.fuzzy_match_threshold == 0.5
        assert state_manager.state.detection_config.format_confidence_threshold == 0.5
        assert state_manager.state.detection_config.sparsity_threshold == 0.5
        assert state_manager.state.detection_config.presidio_confidence_threshold == 0.5

        # Test maximum values
        config_max = DetectionConfig(
            fuzzy_match_threshold=1.0,
            format_confidence_threshold=1.0,
            sparsity_threshold=1.0,
            presidio_confidence_threshold=1.0,
        )

        state_manager.update_state(detection_config=config_max)

        assert state_manager.state.detection_config.fuzzy_match_threshold == 1.0
        assert state_manager.state.detection_config.format_confidence_threshold == 1.0
        assert state_manager.state.detection_config.sparsity_threshold == 1.0
        assert state_manager.state.detection_config.presidio_confidence_threshold == 1.0

    def test_api_key_configuration(self, state_manager):
        """Test API key configuration."""
        # Set API key
        state_manager.set_api_key("test_geonames_username")

        assert state_manager.state.geonames_api_key == "test_geonames_username"

        # Clear API key
        state_manager.set_api_key(None)
        assert state_manager.state.geonames_api_key is None

    def test_configuration_validation_no_methods_selected(self, state_manager):
        """Test validation when no detection methods are selected."""
        # Create config with all methods disabled
        config = DetectionConfig(
            column_name_enabled=False,
            format_pattern_enabled=False,
            sparsity_enabled=False,
            location_population_enabled=False,
            ai_text_enabled=False,
        )

        state_manager.update_state(detection_config=config)

        # Check that at least one method should be enabled for valid config
        any_enabled = any(
            [
                state_manager.state.detection_config.column_name_enabled,
                state_manager.state.detection_config.format_pattern_enabled,
                state_manager.state.detection_config.sparsity_enabled,
                state_manager.state.detection_config.location_population_enabled,
                state_manager.state.detection_config.ai_text_enabled,
            ]
        )

        assert any_enabled is False  # This should trigger validation error in UI

    def test_configuration_with_all_methods(self, state_manager):
        """Test configuration with all detection methods enabled."""
        config = DetectionConfig(
            column_name_enabled=True,
            format_pattern_enabled=True,
            sparsity_enabled=True,
            location_population_enabled=True,
            ai_text_enabled=True,
            fuzzy_match_threshold=0.85,
            format_confidence_threshold=0.8,
            sparsity_threshold=0.75,
            population_threshold=60000,
            presidio_confidence_threshold=0.8,
        )

        state_manager.update_state(detection_config=config)

        # Verify all methods are enabled
        assert state_manager.state.detection_config.column_name_enabled is True
        assert state_manager.state.detection_config.format_pattern_enabled is True
        assert state_manager.state.detection_config.sparsity_enabled is True
        assert state_manager.state.detection_config.location_population_enabled is True
        assert state_manager.state.detection_config.ai_text_enabled is True

        # Verify all thresholds are set
        assert state_manager.state.detection_config.fuzzy_match_threshold == 0.85
        assert state_manager.state.detection_config.format_confidence_threshold == 0.8
        assert state_manager.state.detection_config.sparsity_threshold == 0.75
        assert state_manager.state.detection_config.presidio_confidence_threshold == 0.8

    def test_preset_switching(self, state_manager):
        """Test switching between presets."""
        # Start with quick
        config_quick = DetectionConfig(
            column_name_enabled=True,
            format_pattern_enabled=True,
            sparsity_enabled=False,
            location_population_enabled=False,
            ai_text_enabled=False,
        )
        state_manager.update_state(detection_config=config_quick, preset_mode="quick")
        assert state_manager.state.preset_mode == "quick"

        # Switch to balanced
        config_balanced = DetectionConfig(
            column_name_enabled=True,
            format_pattern_enabled=True,
            sparsity_enabled=True,
            location_population_enabled=False,
            ai_text_enabled=True,
        )
        state_manager.update_state(
            detection_config=config_balanced, preset_mode="balanced"
        )
        assert state_manager.state.preset_mode == "balanced"
        assert state_manager.state.detection_config.sparsity_enabled is True

        # Switch to thorough
        config_thorough = DetectionConfig(
            column_name_enabled=True,
            format_pattern_enabled=True,
            sparsity_enabled=True,
            location_population_enabled=True,
            ai_text_enabled=True,
        )
        state_manager.update_state(
            detection_config=config_thorough, preset_mode="thorough"
        )
        assert state_manager.state.preset_mode == "thorough"
        assert state_manager.state.detection_config.location_population_enabled is True

    def test_language_model_selection(self, state_manager):
        """Test Presidio language model selection."""
        # Test small model
        config_small = DetectionConfig(
            ai_text_enabled=True,
            presidio_language_model="en_core_web_sm",
        )
        state_manager.update_state(detection_config=config_small)
        assert (
            state_manager.state.detection_config.presidio_language_model
            == "en_core_web_sm"
        )

        # Test medium model
        config_medium = DetectionConfig(
            ai_text_enabled=True,
            presidio_language_model="en_core_web_md",
        )
        state_manager.update_state(detection_config=config_medium)
        assert (
            state_manager.state.detection_config.presidio_language_model
            == "en_core_web_md"
        )

        # Test large model
        config_large = DetectionConfig(
            ai_text_enabled=True,
            presidio_language_model="en_core_web_lg",
        )
        state_manager.update_state(detection_config=config_large)
        assert (
            state_manager.state.detection_config.presidio_language_model
            == "en_core_web_lg"
        )

    def test_pattern_type_selective_detection(self, state_manager):
        """Test selective pattern type detection."""
        # Only detect phone and email
        config = DetectionConfig(
            format_pattern_enabled=True,
            detect_phone=True,
            detect_email=True,
            detect_ssn=False,
            detect_dates=False,
        )

        state_manager.update_state(detection_config=config)

        assert state_manager.state.detection_config.detect_phone is True
        assert state_manager.state.detection_config.detect_email is True
        assert state_manager.state.detection_config.detect_ssn is False
        assert state_manager.state.detection_config.detect_dates is False

    def test_presidio_entity_selective_detection(self, state_manager):
        """Test selective Presidio entity detection."""
        # Only detect persons, not organizations
        config = DetectionConfig(
            ai_text_enabled=True,
            presidio_detect_person=True,
            presidio_detect_org=False,
        )

        state_manager.update_state(detection_config=config)

        assert state_manager.state.detection_config.presidio_detect_person is True
        assert state_manager.state.detection_config.presidio_detect_org is False


class TestConfigurationPersistence:
    """Test configuration persistence and state management."""

    @pytest.fixture
    def mock_page(self):
        """Create a mock Flet page."""
        page = Mock()
        page.update = Mock()
        return page

    @pytest.fixture
    def state_manager(self, mock_page):
        """Create a StateManager instance."""
        return StateManager(mock_page)

    def test_configuration_persists_across_navigation(self, state_manager):
        """Test that configuration persists when navigating between screens."""
        # Set configuration
        config = DetectionConfig(
            column_name_enabled=True,
            fuzzy_match_threshold=0.92,
            format_confidence_threshold=0.88,
        )
        state_manager.update_state(detection_config=config)

        # Navigate to different screen
        state_manager.navigate_to("progress")

        # Configuration should persist
        assert state_manager.state.detection_config.fuzzy_match_threshold == 0.92
        assert state_manager.state.detection_config.format_confidence_threshold == 0.88

    def test_configuration_reset(self, state_manager):
        """Test resetting configuration to defaults."""
        # Set custom configuration
        config = DetectionConfig(
            fuzzy_match_threshold=0.95,
            format_confidence_threshold=0.9,
            sparsity_threshold=0.7,
        )
        state_manager.update_state(detection_config=config)

        # Reset to defaults
        default_config = DetectionConfig()
        state_manager.update_state(detection_config=default_config)

        # Should have default values
        assert state_manager.state.detection_config.fuzzy_match_threshold == 0.8
        assert state_manager.state.detection_config.format_confidence_threshold == 0.7
        assert state_manager.state.detection_config.sparsity_threshold == 0.8
