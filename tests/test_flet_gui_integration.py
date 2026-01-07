"""Integration tests for Flet GUI end-to-end workflows."""

from pathlib import Path
from unittest.mock import Mock

import pandas as pd
import pytest

from pii_detector.gui.flet_app.config.settings import (
    DetectionConfig,
    DetectionResult,
    FileInfo,
)
from pii_detector.gui.flet_app.ui.app import StateManager


class TestFileSelectionWorkflow:
    """Test suite for file selection workflow."""

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

    @pytest.fixture
    def sample_csv_file(self, tmp_path):
        """Create a sample CSV file for testing."""
        file_path = tmp_path / "test_data.csv"
        df = pd.DataFrame(
            {
                "name": ["John Doe", "Jane Smith"],
                "email": ["john@test.com", "jane@test.com"],
                "age": [30, 25],
            }
        )
        df.to_csv(file_path, index=False)
        return file_path

    @pytest.fixture
    def sample_excel_file(self, tmp_path):
        """Create a sample Excel file for testing."""
        file_path = tmp_path / "test_data.xlsx"
        df = pd.DataFrame(
            {
                "participant_id": [1, 2, 3],
                "full_name": ["Alice Brown", "Bob Wilson", "Carol Davis"],
                "phone": ["555-1234", "555-5678", "555-9012"],
            }
        )
        df.to_excel(file_path, index=False)
        return file_path

    def test_add_csv_file(self, state_manager, sample_csv_file):
        """Test adding a CSV file to selection."""
        file_info = FileInfo(
            path=sample_csv_file,
            name=sample_csv_file.name,
            size_mb=sample_csv_file.stat().st_size / (1024 * 1024),
            format="csv",
            is_valid=True,
        )

        state_manager.add_file(file_info)

        assert len(state_manager.state.selected_files) == 1
        assert state_manager.state.selected_files[0].format == "csv"
        assert state_manager.state.selected_files[0].is_valid is True

    def test_add_excel_file(self, state_manager, sample_excel_file):
        """Test adding an Excel file to selection."""
        file_info = FileInfo(
            path=sample_excel_file,
            name=sample_excel_file.name,
            size_mb=sample_excel_file.stat().st_size / (1024 * 1024),
            format="xlsx",
            is_valid=True,
        )

        state_manager.add_file(file_info)

        assert len(state_manager.state.selected_files) == 1
        assert state_manager.state.selected_files[0].format == "xlsx"

    def test_add_multiple_files(
        self, state_manager, sample_csv_file, sample_excel_file
    ):
        """Test adding multiple files."""
        csv_info = FileInfo(
            path=sample_csv_file,
            name=sample_csv_file.name,
            size_mb=0.1,
            format="csv",
        )
        excel_info = FileInfo(
            path=sample_excel_file,
            name=sample_excel_file.name,
            size_mb=0.1,
            format="xlsx",
        )

        state_manager.add_file(csv_info)
        state_manager.add_file(excel_info)

        assert len(state_manager.state.selected_files) == 2

    def test_remove_file_from_selection(self, state_manager, sample_csv_file):
        """Test removing a file from selection."""
        file_info = FileInfo(
            path=sample_csv_file,
            name=sample_csv_file.name,
            size_mb=0.1,
            format="csv",
        )

        state_manager.add_file(file_info)
        assert len(state_manager.state.selected_files) == 1

        state_manager.remove_file(sample_csv_file)
        assert len(state_manager.state.selected_files) == 0

    def test_file_validation_invalid_format(self, state_manager, tmp_path):
        """Test file validation for invalid format."""
        invalid_file = tmp_path / "test.txt"
        invalid_file.write_text("This is a text file")

        file_info = FileInfo(
            path=invalid_file,
            name=invalid_file.name,
            size_mb=0.001,
            format="txt",
            is_valid=False,
            validation_message="Unsupported file format",
        )

        state_manager.add_file(file_info)

        assert state_manager.state.selected_files[0].is_valid is False
        assert "Unsupported" in state_manager.state.selected_files[0].validation_message


class TestDetectionWorkflow:
    """Test suite for PII detection workflow."""

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

    @pytest.fixture
    def detection_config(self):
        """Create a detection configuration."""
        return DetectionConfig(
            column_name_enabled=True,
            format_pattern_enabled=True,
            sparsity_enabled=True,
            fuzzy_match_threshold=0.8,
            format_confidence_threshold=0.7,
        )

    def test_start_detection_with_config(self, state_manager, detection_config):
        """Test starting detection with configuration."""
        state_manager.update_state(detection_config=detection_config)
        state_manager.set_processing(True)

        assert state_manager.state.is_processing is True
        assert state_manager.state.detection_config.column_name_enabled is True

    def test_detection_progress_updates(self, state_manager):
        """Test detection progress updates."""
        state_manager.set_processing(True)

        # Update progress at different stages
        state_manager.update_progress(
            progress=0.25,
            stage="Loading file",
            current_file="test.csv",
        )
        assert state_manager.state.current_progress == 0.25
        assert state_manager.state.processing_stage == "Loading file"

        state_manager.update_progress(
            progress=0.5,
            stage="Analyzing columns",
        )
        assert state_manager.state.current_progress == 0.5

        state_manager.update_progress(
            progress=1.0,
            stage="Complete",
        )
        assert state_manager.state.current_progress == 1.0

    def test_add_detection_results(self, state_manager):
        """Test adding detection results."""
        result1 = DetectionResult(
            column="name",
            method="column_name",
            confidence=0.9,
            pii_type="PERSON",
            entity_types=["PERSON"],
        )
        result2 = DetectionResult(
            column="email",
            method="format_pattern",
            confidence=0.95,
            pii_type="EMAIL_ADDRESS",
            entity_types=["EMAIL"],
        )

        state_manager.add_detection_result(result1)
        state_manager.add_detection_result(result2)

        assert len(state_manager.state.detection_results) == 2
        assert state_manager.state.detection_results[0].column == "name"
        assert state_manager.state.detection_results[1].column == "email"

    def test_detection_completion(self, state_manager):
        """Test detection workflow completion."""
        # Start detection
        state_manager.set_processing(True)
        state_manager.update_progress(progress=0.0, stage="Starting")

        # Add results
        result = DetectionResult(
            column="phone",
            method="format_pattern",
            confidence=0.9,
            pii_type="PHONE_NUMBER",
            entity_types=["PHONE"],
        )
        state_manager.add_detection_result(result)

        # Complete detection
        state_manager.update_progress(progress=1.0, stage="Complete")
        state_manager.set_processing(False)

        assert state_manager.state.is_processing is False
        assert len(state_manager.state.detection_results) == 1


class TestReviewAndActionWorkflow:
    """Test suite for results review and action workflow."""

    @pytest.fixture
    def mock_page(self):
        """Create a mock Flet page."""
        page = Mock()
        page.update = Mock()
        return page

    @pytest.fixture
    def state_manager_with_results(self, mock_page):
        """Create a StateManager with detection results."""
        manager = StateManager(mock_page)

        # Add detection results
        results = [
            DetectionResult("name", "column_name", 0.9, "PERSON", ["PERSON"]),
            DetectionResult("email", "format_pattern", 0.95, "EMAIL", ["EMAIL"]),
            DetectionResult("phone", "format_pattern", 0.9, "PHONE", ["PHONE"]),
            DetectionResult("comments", "sparsity", 0.85, "FREETEXT", []),
        ]

        for result in results:
            manager.add_detection_result(result)

        return manager

    def test_set_user_actions(self, state_manager_with_results):
        """Test setting user actions for detected columns."""
        manager = state_manager_with_results

        # Set actions
        manager.set_user_action("name", "remove")
        manager.set_user_action("email", "encode")
        manager.set_user_action("phone", "mask")
        manager.set_user_action("comments", "keep")

        assert manager.state.user_actions["name"] == "remove"
        assert manager.state.user_actions["email"] == "encode"
        assert manager.state.user_actions["phone"] == "mask"
        assert manager.state.user_actions["comments"] == "keep"

    def test_set_anonymization_methods(self, state_manager_with_results):
        """Test setting anonymization methods for columns."""
        manager = state_manager_with_results

        # Set anonymization methods
        manager.state.column_anonymization_methods["name"] = "remove"
        manager.state.column_anonymization_methods["email"] = "hash"
        manager.state.column_anonymization_methods["phone"] = "pattern_mask"

        assert manager.state.column_anonymization_methods["name"] == "remove"
        assert manager.state.column_anonymization_methods["email"] == "hash"
        assert manager.state.column_anonymization_methods["phone"] == "pattern_mask"

    def test_change_user_action(self, state_manager_with_results):
        """Test changing user action for a column."""
        manager = state_manager_with_results

        # Initial action
        manager.set_user_action("email", "remove")
        assert manager.state.user_actions["email"] == "remove"

        # Change action
        manager.set_user_action("email", "encode")
        assert manager.state.user_actions["email"] == "encode"


class TestNavigationWorkflow:
    """Test suite for screen navigation workflow."""

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

    def test_complete_workflow_navigation(self, state_manager):
        """Test navigation through complete workflow."""
        # Start at dashboard
        assert state_manager.state.current_screen == "dashboard"

        # Navigate to file selection
        state_manager.navigate_to("file_selection")
        assert state_manager.state.current_screen == "file_selection"
        assert "dashboard" in state_manager.state.screen_history

        # Navigate to configuration
        state_manager.navigate_to("configuration")
        assert state_manager.state.current_screen == "configuration"
        assert "file_selection" in state_manager.state.screen_history

        # Navigate to progress
        state_manager.navigate_to("progress")
        assert state_manager.state.current_screen == "progress"

        # Navigate to results
        state_manager.navigate_to("results")
        assert state_manager.state.current_screen == "results"

        # Navigate to export
        state_manager.navigate_to("export")
        assert state_manager.state.current_screen == "export"

    def test_back_navigation(self, state_manager):
        """Test back navigation through workflow."""
        # Navigate forward
        state_manager.navigate_to("file_selection")
        state_manager.navigate_to("configuration")
        state_manager.navigate_to("progress")

        # Navigate back
        state_manager.go_back()
        assert state_manager.state.current_screen == "configuration"

        state_manager.go_back()
        assert state_manager.state.current_screen == "file_selection"

        state_manager.go_back()
        assert state_manager.state.current_screen == "dashboard"


class TestErrorHandling:
    """Test suite for error handling and validation."""

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

    def test_add_error_message(self, state_manager):
        """Test adding error messages."""
        state_manager.add_error_message("File validation failed")
        state_manager.add_error_message("Detection error")

        assert len(state_manager.state.error_messages) == 2
        assert "File validation failed" in state_manager.state.error_messages

    def test_add_success_message(self, state_manager):
        """Test adding success messages."""
        state_manager.add_success_message("File loaded successfully")
        state_manager.add_success_message("Detection complete")

        assert len(state_manager.state.success_messages) == 2
        assert "File loaded successfully" in state_manager.state.success_messages

    def test_clear_messages(self, state_manager):
        """Test clearing messages."""
        state_manager.add_error_message("Error 1")
        state_manager.add_success_message("Success 1")

        assert len(state_manager.state.error_messages) == 1
        assert len(state_manager.state.success_messages) == 1

        state_manager.clear_messages()

        assert len(state_manager.state.error_messages) == 0
        assert len(state_manager.state.success_messages) == 0


class TestBackendIntegration:
    """Test suite for backend adapter integration."""

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

    @pytest.fixture
    def sample_dataframe(self):
        """Create a sample dataframe."""
        return pd.DataFrame(
            {
                "participant_name": ["John Doe", "Jane Smith", "Bob Wilson"],
                "email_address": ["john@test.com", "jane@test.com", "bob@test.com"],
                "phone_number": ["555-1234", "555-5678", "555-9012"],
                "age_years": [30, 25, 35],
                "survey_notes": ["Note 1", "Note 2", "Note 3"],
            }
        )

    def test_config_to_backend_mapping(self, state_manager):
        """Test mapping GUI config to backend processor config."""
        # Set GUI configuration
        gui_config = DetectionConfig(
            column_name_enabled=True,
            format_pattern_enabled=True,
            sparsity_enabled=True,
            ai_text_enabled=True,
            fuzzy_match_threshold=0.85,
            format_confidence_threshold=0.8,
            sparsity_threshold=0.75,
            presidio_confidence_threshold=0.8,
        )

        state_manager.update_state(detection_config=gui_config)

        # Verify configuration values are accessible
        config = state_manager.state.detection_config

        assert config.column_name_enabled is True
        assert config.fuzzy_match_threshold == 0.85
        assert config.format_confidence_threshold == 0.8
        assert config.sparsity_threshold == 0.75
        assert config.presidio_confidence_threshold == 0.8

    def test_detection_results_from_backend(self, state_manager):
        """Test receiving detection results from backend."""
        # Simulate backend returning detection results
        backend_results = [
            {
                "column": "participant_name",
                "method": "column_name_matching",
                "confidence": 0.9,
                "pii_type": "PERSON",
                "entity_types": ["PERSON"],
            },
            {
                "column": "email_address",
                "method": "format_patterns",
                "confidence": 0.95,
                "pii_type": "EMAIL_ADDRESS",
                "entity_types": ["EMAIL"],
            },
        ]

        # Convert to DetectionResult objects
        for result in backend_results:
            detection_result = DetectionResult(
                column=result["column"],
                method=result["method"],
                confidence=result["confidence"],
                pii_type=result["pii_type"],
                entity_types=result["entity_types"],
            )
            state_manager.add_detection_result(detection_result)

        assert len(state_manager.state.detection_results) == 2
        assert state_manager.state.detection_results[0].column == "participant_name"
        assert state_manager.state.detection_results[1].column == "email_address"


class TestStateReset:
    """Test suite for state reset and cleanup."""

    @pytest.fixture
    def mock_page(self):
        """Create a mock Flet page."""
        page = Mock()
        page.update = Mock()
        return page

    @pytest.fixture
    def populated_state_manager(self, mock_page):
        """Create a StateManager with populated state."""
        manager = StateManager(mock_page)

        # Add files
        file_info = FileInfo(
            path=Path("test.csv"),
            name="test.csv",
            size_mb=1.0,
            format="csv",
        )
        manager.add_file(file_info)

        # Set configuration
        config = DetectionConfig(fuzzy_match_threshold=0.95)
        manager.update_state(detection_config=config)

        # Add results
        result = DetectionResult("name", "column_name", 0.9, "PERSON", ["PERSON"])
        manager.add_detection_result(result)

        # Add messages
        manager.add_error_message("Test error")
        manager.add_success_message("Test success")

        # Set processing state
        manager.set_processing(True)

        return manager

    def test_reset_state(self, populated_state_manager):
        """Test resetting state to defaults."""
        manager = populated_state_manager

        # Verify state is populated
        assert len(manager.state.selected_files) == 1
        assert len(manager.state.detection_results) == 1
        assert len(manager.state.error_messages) == 1
        assert manager.state.is_processing is True

        # Reset state
        manager.reset_state()

        # Verify state is reset
        assert len(manager.state.selected_files) == 0
        assert len(manager.state.detection_results) == 0
        assert len(manager.state.error_messages) == 0
        assert manager.state.is_processing is False
        assert manager.state.current_screen == "dashboard"
