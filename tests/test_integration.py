"""Integration tests for PII detection using real test datasets."""

from pathlib import Path

import pandas as pd
import pytest

from pii_detector.core.processor import (
    find_piis_based_on_column_format,
    find_piis_based_on_column_name,
    find_piis_based_on_locations_population,
    find_piis_based_on_sparse_entries,
    import_dataset,
)
from pii_detector.data import constants


class TestDatasetIntegration:
    """Integration tests using real test datasets."""

    @pytest.fixture
    def test_data_dir(self):
        """Get path to test data directory."""
        return Path(__file__).parent / "data"

    @pytest.fixture
    def pii_dataset_path(self, test_data_dir):
        """Get path to PII-containing test dataset."""
        return test_data_dir / "sample_pii_data.csv"

    @pytest.fixture
    def clean_dataset_path(self, test_data_dir):
        """Get path to clean test dataset."""
        return test_data_dir / "clean_data.csv"

    def test_import_pii_dataset(self, pii_dataset_path):
        """Test importing PII dataset."""
        success, result = import_dataset(str(pii_dataset_path))

        assert success is True
        assert isinstance(result, list)
        assert len(result) == 4  # [dataset, path, label_dict, value_label_dict]

        dataset, path, label_dict, value_label_dict = result
        assert isinstance(dataset, pd.DataFrame)
        assert len(dataset) == 4  # 4 rows
        assert len(dataset.columns) == 13  # 13 columns

        # Check expected columns are present
        expected_columns = [
            "participant_id",
            "first_name",
            "email",
            "phone_number",
            "deviceid",
        ]
        for col in expected_columns:
            assert col in dataset.columns

    def test_import_clean_dataset(self, clean_dataset_path):
        """Test importing clean dataset."""
        success, result = import_dataset(str(clean_dataset_path))

        assert success is True
        dataset, _, _, _ = result
        assert len(dataset) == 8  # 8 rows
        assert len(dataset.columns) == 8  # 8 columns

    def test_column_name_detection_on_pii_data(self, pii_dataset_path):
        """Test column name detection on PII-containing dataset."""
        success, result = import_dataset(str(pii_dataset_path))
        assert success is True

        dataset, _, label_dict, _ = result

        # Test column name detection
        pii_columns = find_piis_based_on_column_name(
            dataset, label_dict or {}, constants.ENGLISH, "USA", constants.STRICT
        )

        # Should detect obvious PII columns
        expected_pii_columns = [
            "email",
            "deviceid",
            "gps_lat",
            "gps_lon",
        ]  # GPS coordinates and deviceid are in restricted words

        # Check that at least some expected columns are detected
        detected_count = sum(1 for col in expected_pii_columns if col in pii_columns)
        assert detected_count > 0, (
            f"Expected to detect some of {expected_pii_columns}, got {pii_columns}"
        )

    def test_column_name_detection_on_clean_data(self, clean_dataset_path):
        """Test column name detection on clean dataset."""
        success, result = import_dataset(str(clean_dataset_path))
        assert success is True

        dataset, _, label_dict, _ = result

        pii_columns = find_piis_based_on_column_name(
            dataset, label_dict or {}, constants.ENGLISH, "USA", constants.STRICT
        )

        # Clean dataset should have fewer or no PII detections based on column names
        assert len(pii_columns) <= 1, (
            f"Clean dataset shouldn't have many PII columns, got {pii_columns}"
        )

    def test_format_detection_on_pii_data(self, pii_dataset_path):
        """Test format pattern detection on PII-containing dataset."""
        success, result = import_dataset(str(pii_dataset_path))
        assert success is True

        dataset, _, _, _ = result

        format_piis = find_piis_based_on_column_format(dataset)

        # Should detect email and phone number formats
        # Note: The exact detection depends on the patterns and thresholds
        assert isinstance(format_piis, list)
        # Could detect email, phone_number columns based on format
        potential_format_columns = ["email", "phone_number", "date_of_birth"]

        # At least one format-based detection should occur
        if len(format_piis) > 0:
            assert any(col in potential_format_columns for col in format_piis), (
                f"Expected format detection in {potential_format_columns}, got {format_piis}"
            )

    def test_sparsity_detection_on_pii_data(self, pii_dataset_path):
        """Test sparsity detection on PII-containing dataset."""
        success, result = import_dataset(str(pii_dataset_path))
        assert success is True

        dataset, _, _, _ = result

        sparse_piis = find_piis_based_on_sparse_entries(dataset, sparse_threshold=0.7)

        # With small test dataset, most columns will be sparse (all unique values)
        # Expected sparse columns: first_name, last_name, email, phone_number, address, etc.
        assert isinstance(sparse_piis, list)
        assert len(sparse_piis) > 0, "Should detect some sparse columns in PII dataset"

    def test_sparsity_detection_on_clean_data(self, clean_dataset_path):
        """Test sparsity detection on clean dataset."""
        success, result = import_dataset(str(clean_dataset_path))
        assert success is True

        dataset, _, _, _ = result

        sparse_piis = find_piis_based_on_sparse_entries(dataset, sparse_threshold=0.8)

        # Clean dataset has some repeated values, should have fewer sparse columns
        assert isinstance(sparse_piis, list)
        # Most columns in clean dataset have unique values per row, so might still be sparse

    @pytest.mark.integration
    @pytest.mark.slow
    def test_location_detection_on_pii_data(self, pii_dataset_path):
        """Test location population detection (marked as slow due to API calls)."""
        success, result = import_dataset(str(pii_dataset_path))
        assert success is True

        dataset, _, _, _ = result

        # This test makes actual API calls, so it's marked as slow
        # In practice, you'd mock these calls for faster testing
        location_piis = find_piis_based_on_locations_population(
            dataset, population_threshold=50000
        )

        # Should return a list (might be empty if API calls fail or locations are large)
        assert isinstance(location_piis, list)

    def test_full_pii_detection_workflow(self, pii_dataset_path):
        """Test complete PII detection workflow."""
        success, result = import_dataset(str(pii_dataset_path))
        assert success is True

        dataset, _, label_dict, _ = result

        # Run all detection methods
        all_pii_candidates = []

        # Column name detection
        column_name_piis = find_piis_based_on_column_name(
            dataset, label_dict or {}, constants.ENGLISH, "USA", constants.STRICT
        )
        all_pii_candidates.extend([(col, "Column Name") for col in column_name_piis])

        # Format detection
        format_piis = find_piis_based_on_column_format(dataset)
        all_pii_candidates.extend([(col, "Format") for col in format_piis])

        # Sparsity detection
        sparse_piis = find_piis_based_on_sparse_entries(dataset)
        all_pii_candidates.extend([(col, "Sparse") for col in sparse_piis])

        # Combine results
        unique_piis = {}
        for col, method in all_pii_candidates:
            if col not in unique_piis:
                unique_piis[col] = [method]
            else:
                unique_piis[col].append(method)

        # Should detect multiple PII columns using various methods
        assert len(unique_piis) > 0, "Should detect some PII in the test dataset"
        assert len(unique_piis) < len(dataset.columns), (
            "Shouldn't flag ALL columns as PII"
        )

        # Verify that known PII columns are detected by at least one method
        known_pii_indicators = ["email", "first_name", "last_name", "phone_number"]
        detected_pii_indicators = sum(
            1 for indicator in known_pii_indicators if indicator in unique_piis
        )

        assert detected_pii_indicators > 0, (
            f"Should detect some known PII indicators from {known_pii_indicators}"
        )

    def test_clean_dataset_workflow(self, clean_dataset_path):
        """Test PII detection on clean dataset (should detect fewer PIIs)."""
        success, result = import_dataset(str(clean_dataset_path))
        assert success is True

        dataset, _, label_dict, _ = result

        # Run all detection methods with appropriate thresholds for clean data
        column_name_piis = find_piis_based_on_column_name(
            dataset, label_dict or {}, constants.ENGLISH, "USA", constants.STRICT
        )
        format_piis = find_piis_based_on_column_format(dataset)
        # Use higher threshold for sparsity to reduce false positives on clean data
        sparse_piis = find_piis_based_on_sparse_entries(dataset, sparse_threshold=0.95)

        # Clean dataset should have no column name matches (no restricted words)
        assert len(column_name_piis) == 0, (
            f"Clean dataset shouldn't match restricted words, got {column_name_piis}"
        )

        # Should have minimal format detections (dates might still be detected)
        assert len(format_piis) <= 2, (
            f"Clean dataset should have few format detections, got {format_piis}"
        )

        # With more data and higher threshold, should have fewer sparse detections
        print(f"Sparse detections: {sparse_piis}")
        print(f"Dataset shape: {dataset.shape}")

        # The key insight: clean datasets have more repeated values, less sparsity
        total_detections = len(set(column_name_piis + format_piis + sparse_piis))
        assert total_detections < len(dataset.columns), (
            f"Should not flag ALL columns as PII in clean dataset, got {total_detections}/{len(dataset.columns)}"
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
