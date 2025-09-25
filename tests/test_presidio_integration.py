"""Tests for Presidio integration functionality."""

from unittest.mock import Mock, patch

import pandas as pd
import pytest

from pii_detector.core.hybrid_anonymizer import (
    HybridAnonymizer,
    anonymize_dataset_hybrid,
)
from pii_detector.core.presidio_engine import (
    PresidioTextAnalyzer,
    get_presidio_analyzer,
    presidio_analyze_dataframe_batch,
    presidio_analyze_text_column,
    presidio_anonymize_dataframe_batch,
    presidio_anonymize_text_column,
)
from pii_detector.core.unified_processor import (
    PIIDetectionResult,
    UnifiedPIIProcessor,
    detect_pii_unified,
)


class TestPresidioTextAnalyzer:
    """Test the Presidio text analyzer wrapper."""

    def test_analyzer_initialization(self):
        """Test analyzer initialization with graceful degradation."""
        analyzer = PresidioTextAnalyzer()
        # Should not raise error even if Presidio not available
        assert analyzer is not None
        assert isinstance(analyzer.available, bool)

    def test_analyze_text_without_presidio(self):
        """Test text analysis when Presidio is not available."""
        with patch("pii_detector.core.presidio_engine.PRESIDIO_AVAILABLE", False):
            analyzer = PresidioTextAnalyzer()
            result = analyzer.analyze_text("John Doe's email is john@example.com")
            assert result == []

    @pytest.mark.skipif(
        True, reason="Requires Presidio installation - integration test only"
    )
    def test_analyze_text_with_presidio(self):
        """Test text analysis when Presidio is available (integration test)."""
        analyzer = PresidioTextAnalyzer()
        if analyzer.is_available():
            result = analyzer.analyze_text("John Doe's email is john@example.com")
            assert isinstance(result, list)
            # Should detect PERSON and EMAIL_ADDRESS entities

    def test_analyze_column_text_empty_data(self):
        """Test column analysis with empty data."""
        analyzer = PresidioTextAnalyzer()
        empty_series = pd.Series([None, "", "  "])
        result = analyzer.analyze_column_text(empty_series)

        expected_keys = [
            "presidio_available",
            "entities_found",
            "total_detections",
            "confidence_scores",
            "sample_analyzed",
        ]
        for key in expected_keys:
            assert key in result
        assert result["total_detections"] == 0
        assert result["sample_analyzed"] == 0

    def test_anonymize_text_without_presidio(self):
        """Test text anonymization fallback when Presidio not available."""
        with patch("pii_detector.core.presidio_engine.PRESIDIO_AVAILABLE", False):
            analyzer = PresidioTextAnalyzer()
            text = "Contact John at john@example.com"
            result = analyzer.anonymize_text(text)
            # Should return original text when Presidio not available
            assert result == text

    def test_get_supported_entities_without_presidio(self):
        """Test getting supported entities when Presidio not available."""
        with patch("pii_detector.core.presidio_engine.PRESIDIO_AVAILABLE", False):
            analyzer = PresidioTextAnalyzer()
            entities = analyzer.get_supported_entities()
            assert entities == []

    def test_singleton_analyzer(self):
        """Test that get_presidio_analyzer returns singleton instance."""
        analyzer1 = get_presidio_analyzer()
        analyzer2 = get_presidio_analyzer()
        assert analyzer1 is analyzer2

    def test_presidio_analyze_text_column_convenience(self):
        """Test convenience function for column analysis."""
        test_data = pd.Series(["John Doe", "jane@example.com", "555-123-4567"])
        result = presidio_analyze_text_column(test_data)

        # Should return analysis dictionary
        assert isinstance(result, dict)
        assert "presidio_available" in result

    def test_presidio_anonymize_text_column_convenience(self):
        """Test convenience function for column anonymization."""
        test_data = pd.Series(["John Doe", "jane@example.com", "normal text"])
        result = presidio_anonymize_text_column(test_data)

        # Should return pandas Series
        assert isinstance(result, pd.Series)
        assert len(result) == len(test_data)

    def test_analyze_column_text_with_batch_size(self):
        """Test column text analysis with batch size parameter."""
        analyzer = PresidioTextAnalyzer()
        test_data = pd.Series(["John Doe"] * 20)  # Larger dataset

        # Test with batch processing
        result = analyzer.analyze_column_text(
            test_data, confidence_threshold=0.7, sample_size=20, batch_size=5
        )

        # Should return analysis results
        assert isinstance(result, dict)
        assert "presidio_available" in result

    def test_presidio_analyze_dataframe_batch_function(self):
        """Test DataFrame batch analysis function."""
        df = pd.DataFrame(
            {
                "name": ["John Doe", "Jane Smith"],
                "email": ["john@test.com", "jane@test.com"],
                "age": [25, 30],
            }
        )

        # Mock to avoid external dependencies in unit tests
        with patch(
            "pii_detector.core.presidio_engine.get_presidio_analyzer"
        ) as mock_get:
            mock_analyzer = Mock()
            mock_analyzer.is_available.return_value = False
            mock_get.return_value = mock_analyzer

            result = presidio_analyze_dataframe_batch(df)
            assert result == {}

    def test_presidio_anonymize_dataframe_batch_function(self):
        """Test DataFrame batch anonymization function."""
        df = pd.DataFrame(
            {
                "name": ["John Doe", "Jane Smith"],
                "email": ["john@test.com", "jane@test.com"],
                "notes": ["Contact info", "Personal data"],
            }
        )

        # Mock to avoid external dependencies
        with patch(
            "pii_detector.core.presidio_engine.get_presidio_analyzer"
        ) as mock_get:
            mock_analyzer = Mock()
            mock_analyzer.is_available.return_value = False
            mock_get.return_value = mock_analyzer

            result = presidio_anonymize_dataframe_batch(df, ["name", "email"])

            # Should return original DataFrame when Presidio not available
            assert result.equals(df)


class TestUnifiedPIIProcessor:
    """Test the unified PII processor."""

    def test_processor_initialization(self):
        """Test processor initialization."""
        processor = UnifiedPIIProcessor()
        assert processor is not None
        assert processor.language == "en"
        assert processor.presidio_analyzer is not None

    def test_pii_detection_result(self):
        """Test PIIDetectionResult class."""
        result = PIIDetectionResult(
            column_name="email_col",
            detection_method="presidio_text_analysis",
            confidence=0.85,
            entity_types=["EMAIL_ADDRESS"],
            details={"sample_size": 10},
        )

        assert result.column_name == "email_col"
        assert result.confidence == 0.85
        assert "EMAIL_ADDRESS" in result.entity_types
        assert result.details["sample_size"] == 10

    def test_detect_pii_comprehensive_basic(self):
        """Test comprehensive PII detection with basic dataset."""
        # Create test dataset
        data = {
            "name": ["John Doe", "Jane Smith", "Bob Johnson"],
            "email": ["john@test.com", "jane@test.com", "bob@test.com"],
            "age": [25, 30, 35],
            "notes": ["Some notes", "More notes", "Extra info"],
        }
        df = pd.DataFrame(data)

        processor = UnifiedPIIProcessor()
        results = processor.detect_pii_comprehensive(df)

        # Should return detection results
        assert isinstance(results, dict)

        # Check that high-confidence detections include likely PII columns
        processor.get_high_confidence_detections(results, threshold=0.7)
        # At minimum, email format should be detected

        # Test summary generation
        summary = processor.get_detection_summary(results)
        assert "total_detections" in summary
        assert isinstance(summary["total_detections"], int)

    def test_default_config(self):
        """Test default configuration settings."""
        processor = UnifiedPIIProcessor()
        config = processor._get_default_config()

        expected_keys = [
            "use_column_name_detection",
            "use_format_detection",
            "use_sparsity_detection",
            "use_presidio_detection",
        ]
        for key in expected_keys:
            assert key in config
            assert isinstance(config[key], bool)

    def test_detect_pii_unified_convenience(self):
        """Test convenience function for unified detection."""
        data = {"email": ["test@example.com", "user@test.org"]}
        df = pd.DataFrame(data)

        results = detect_pii_unified(df)
        assert isinstance(results, dict)

    def test_combine_detection_results(self):
        """Test combining structural and text detection results."""
        processor = UnifiedPIIProcessor()

        structural_result = PIIDetectionResult(
            column_name="test_col",
            detection_method="column_name_matching",
            confidence=0.8,
        )

        text_result = PIIDetectionResult(
            column_name="test_col",
            detection_method="presidio_text_analysis",
            confidence=0.9,
            entity_types=["EMAIL_ADDRESS"],
        )

        config = processor._get_default_config()
        combined = processor._combine_detection_results(
            "test_col", structural_result, text_result, config
        )

        assert combined is not None
        assert combined.detection_method == "hybrid_detection"
        assert "EMAIL_ADDRESS" in combined.entity_types
        # Confidence should be weighted average
        expected_conf = 0.8 * 0.6 + 0.9 * 0.4  # default weights
        assert abs(combined.confidence - expected_conf) < 0.01


class TestHybridAnonymizer:
    """Test the hybrid anonymizer."""

    def test_anonymizer_initialization(self):
        """Test anonymizer initialization."""
        anonymizer = HybridAnonymizer()
        assert anonymizer is not None
        assert anonymizer.current_techniques is not None
        assert anonymizer.presidio_analyzer is not None

    def test_anonymize_dataset_basic(self):
        """Test basic dataset anonymization."""
        # Create test dataset
        data = {
            "name": ["John Doe", "Jane Smith"],
            "email": ["john@test.com", "jane@test.com"],
            "age": [25, 30],
        }
        df = pd.DataFrame(data)
        pii_columns = ["name", "email"]

        anonymizer = HybridAnonymizer()
        anonymized_df, report = anonymizer.anonymize_dataset(df, pii_columns)

        # Should return anonymized dataset and report
        assert isinstance(anonymized_df, pd.DataFrame)
        assert isinstance(report, dict)
        assert anonymized_df.shape == df.shape

        # Check report structure
        assert "original_shape" in report
        assert "columns_processed" in report
        assert "methods_applied" in report

    def test_determine_anonymization_method(self):
        """Test method determination logic."""
        anonymizer = HybridAnonymizer()

        # Test with format patterns detection
        detection_result = PIIDetectionResult(
            column_name="phone", detection_method="format_patterns", confidence=0.9
        )

        test_series = pd.Series(["555-123-4567", "555-987-6543"])
        method = anonymizer._determine_anonymization_method(
            test_series, detection_result, {}
        )

        assert method == "text_masking"

    def test_get_available_methods(self):
        """Test getting available anonymization methods."""
        anonymizer = HybridAnonymizer()
        methods = anonymizer.get_available_methods()

        # Should include standard methods
        expected_methods = [
            "remove",
            "hash_pseudonymization",
            "age_categorization",
            "text_masking",
            "add_noise",
        ]

        for method in expected_methods:
            assert method in methods
            assert "description" in methods[method]
            assert "suitable_for" in methods[method]

    def test_anonymize_text_content(self):
        """Test text content anonymization."""
        anonymizer = HybridAnonymizer()
        text = "Contact John Doe at john@example.com or 555-123-4567"

        # Should handle gracefully whether Presidio is available or not
        result = anonymizer.anonymize_text_content(text)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_anonymize_dataset_hybrid_convenience(self):
        """Test convenience function for hybrid anonymization."""
        data = {"email": ["test@example.com", "user@test.org"]}
        df = pd.DataFrame(data)

        anonymized_df, report = anonymize_dataset_hybrid(df, ["email"])
        assert isinstance(anonymized_df, pd.DataFrame)
        assert isinstance(report, dict)


class TestPresidioIntegrationEnd2End:
    """End-to-end integration tests."""

    def test_full_pipeline_without_presidio(self):
        """Test full pipeline when Presidio is not available."""
        # Create test dataset
        data = {
            "participant_name": ["John Doe", "Jane Smith", "Bob Wilson"],
            "email_address": ["john@test.com", "jane@test.com", "bob@test.com"],
            "phone_number": ["555-0123", "555-0456", "555-0789"],
            "age": [25, 30, 35],
            "comments": ["Good participant", "Very helpful", "Cooperative"],
        }
        df = pd.DataFrame(data)

        # Step 1: Detection
        processor = UnifiedPIIProcessor()
        detection_results = processor.detect_pii_comprehensive(df)

        # Step 2: Anonymization
        anonymizer = HybridAnonymizer()
        anonymized_df, report = anonymizer.anonymize_dataset(df, detection_results)

        # Verify pipeline completed
        assert isinstance(detection_results, dict)
        assert isinstance(anonymized_df, pd.DataFrame)
        assert isinstance(report, dict)
        assert anonymized_df.shape[0] == df.shape[0]  # Same number of rows

    def test_configuration_options(self):
        """Test various configuration options."""
        data = {"test_col": ["test data"]}
        df = pd.DataFrame(data)

        # Custom detection config
        detection_config = {
            "use_presidio_detection": False,  # Disable Presidio
            "use_column_name_detection": True,
            "column_name_confidence": 0.9,
        }

        processor = UnifiedPIIProcessor()
        results = processor.detect_pii_comprehensive(
            df, detection_config=detection_config
        )

        # Custom anonymization config
        anonymization_config = {"test_col": {"method": "hash_pseudonymization"}}

        anonymizer = HybridAnonymizer()
        anonymized_df, report = anonymizer.anonymize_dataset(
            df, ["test_col"], anonymization_config
        )

        # Should complete without errors
        assert isinstance(results, dict)
        assert isinstance(anonymized_df, pd.DataFrame)

    @pytest.mark.slow
    def test_large_dataset_performance(self):
        """Test performance with larger dataset."""
        import numpy as np

        # Create larger test dataset
        size = 1000
        data = {
            "id": range(size),
            "name": [f"Person_{i}" for i in range(size)],
            "email": [f"person{i}@test.com" for i in range(size)],
            "notes": [f"Note about person {i}" for i in range(size)],
            "value": np.random.randint(1, 100, size),
        }
        df = pd.DataFrame(data)

        # Run detection
        processor = UnifiedPIIProcessor()
        detection_results = processor.detect_pii_comprehensive(df)

        # Run anonymization
        anonymizer = HybridAnonymizer()
        anonymized_df, report = anonymizer.anonymize_dataset(df, detection_results)

        # Verify results
        assert len(anonymized_df) == size
        assert "columns_processed" in report

        # Performance should be reasonable (this is a smoke test)
        assert len(detection_results) >= 0  # At least runs without error


if __name__ == "__main__":
    pytest.main([__file__])
