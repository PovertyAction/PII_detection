"""Tests for batch processing functionality."""

from unittest.mock import Mock, patch

import numpy as np
import pandas as pd
import pytest

from pii_detector.core.batch_processor import BatchPIIProcessor, process_dataset_batch
from pii_detector.core.presidio_engine import (
    presidio_analyze_dataframe_batch,
    presidio_anonymize_dataframe_batch,
)
from pii_detector.core.unified_processor import PIIDetectionResult


class TestBatchPIIProcessor:
    """Test the batch PII processor."""

    def test_processor_initialization(self):
        """Test batch processor initialization with various configurations."""
        # Default initialization
        processor = BatchPIIProcessor()
        assert processor is not None
        assert processor.language == "en"
        assert processor.chunk_size == 1000
        assert processor.max_workers == 4

        # Custom initialization
        processor_custom = BatchPIIProcessor(
            language="es", chunk_size=500, max_workers=2, use_structured_engine=False
        )
        assert processor_custom.language == "es"
        assert processor_custom.chunk_size == 500
        assert processor_custom.max_workers == 2
        assert processor_custom.use_structured_engine is False

    def test_get_processing_strategy(self):
        """Test processing strategy selection logic."""
        processor = BatchPIIProcessor(chunk_size=1000)

        # Small dataset - standard processing
        small_df = pd.DataFrame({"col1": range(100)})
        strategy = processor.get_processing_strategy(small_df)
        assert strategy == "standard_processing"

        # Large dataset - chunked processing
        large_df = pd.DataFrame({"col1": range(3000)})
        strategy = processor.get_processing_strategy(large_df)
        assert strategy == "chunked_processing"

    def test_estimate_processing_time(self):
        """Test processing time estimation."""
        processor = BatchPIIProcessor()

        # Create test dataset
        df = pd.DataFrame({"text_col": ["sample text"] * 500, "num_col": range(500)})

        estimates = processor.estimate_processing_time(df)

        # Should return estimates dictionary
        assert isinstance(estimates, dict)
        assert "standard_processing" in estimates
        assert "chunked_processing" in estimates

        for strategy, estimate in estimates.items():
            assert "time_seconds" in estimate
            assert "memory_mb" in estimate
            assert "recommended" in estimate
            assert isinstance(estimate["time_seconds"], (int, float))
            assert isinstance(estimate["memory_mb"], (int, float))
            assert isinstance(estimate["recommended"], bool)

    def create_test_dataset(self, size: int = 1000) -> pd.DataFrame:
        """Create synthetic dataset for testing."""
        np.random.seed(42)

        data = {
            "id": range(1, size + 1),
            "name": [f"Person {i}" for i in range(size)],
            "email": [f"person{i}@test.com" for i in range(size)],
            "phone": [f"555-{i:04d}" for i in range(size)],
            "address": [f"{i} Main St, City, State" for i in range(size)],
            "age": np.random.randint(18, 80, size),
            "salary": np.random.randint(30000, 150000, size),
            "comments": [f"Comment about person {i}" for i in range(size)],
            "notes": [f"Additional notes for {i}" for i in range(size)],
        }

        return pd.DataFrame(data)

    def test_detect_pii_batch_small_dataset(self):
        """Test batch detection on small dataset (standard processing)."""
        processor = BatchPIIProcessor(chunk_size=1000)  # Large chunk = no chunking
        df = self.create_test_dataset(500)  # Small dataset

        progress_calls = []

        def progress_callback(percent, message):
            progress_calls.append((percent, message))

        results = processor.detect_pii_batch(df, progress_callback=progress_callback)

        # Should return detection results
        assert isinstance(results, dict)
        assert len(results) > 0  # Should find some PII

        # Check that some expected PII columns are detected
        expected_pii_cols = ["name", "email", "phone", "address"]
        found_pii = [col for col in expected_pii_cols if col in results]
        assert len(found_pii) > 0, (
            f"Expected to find PII in {expected_pii_cols}, got {list(results.keys())}"
        )

        # Progress should have been called
        assert len(progress_calls) > 0

        # Verify result structure
        for col_name, result in results.items():
            assert isinstance(result, PIIDetectionResult)
            assert result.column_name == col_name
            assert 0 <= result.confidence <= 1
            assert result.detection_method is not None

    def test_detect_pii_batch_large_dataset_chunked(self):
        """Test batch detection on large dataset (chunked processing)."""
        processor = BatchPIIProcessor(chunk_size=300, max_workers=2)
        df = self.create_test_dataset(1000)  # Large dataset

        progress_calls = []

        def progress_callback(percent, message):
            progress_calls.append((percent, message))

        results = processor.detect_pii_batch(df, progress_callback=progress_callback)

        # Should return detection results
        assert isinstance(results, dict)
        assert len(results) > 0

        # Should have used chunked processing (multiple progress updates)
        assert len(progress_calls) > 1

        # Verify that chunked processing produces similar results to standard
        # by checking that major PII columns are still detected
        expected_pii_cols = ["name", "email", "phone", "address"]
        found_pii = [col for col in expected_pii_cols if col in results]
        assert len(found_pii) > 0

    def test_detect_with_custom_config(self):
        """Test batch detection with custom configuration."""
        processor = BatchPIIProcessor()
        df = self.create_test_dataset(200)

        # Custom detection config
        detection_config = {
            "use_presidio_detection": False,  # Disable Presidio for consistent testing
            "use_column_name_detection": True,
            "use_format_detection": True,
            "use_sparsity_detection": False,  # Disable to reduce variability
            "use_location_detection": False,  # Disable to reduce external dependencies
            "column_name_confidence": 0.9,
            "format_pattern_confidence": 0.95,
        }

        results = processor.detect_pii_batch(df, detection_config=detection_config)

        assert isinstance(results, dict)
        # With restricted detection methods, should still find some PII
        # (at minimum, format patterns like email should be detected)

    def test_analyze_chunk_text_content(self):
        """Test chunk text content analysis."""
        processor = BatchPIIProcessor()

        # Create chunk with text data
        chunk_data = {
            "text_col1": ["John Doe", "jane@example.com", "normal text"],
            "text_col2": ["555-123-4567", "more text", "even more text"],
            "num_col": [1, 2, 3],
        }
        chunk = pd.DataFrame(chunk_data)
        text_columns = ["text_col1", "text_col2"]

        config = processor._get_optimized_detection_config()

        # Mock the presidio analyzer to avoid external dependencies
        with (
            patch.object(
                processor.presidio_analyzer, "is_available", return_value=True
            ),
            patch.object(
                processor.presidio_analyzer, "analyze_column_text"
            ) as mock_analyze,
        ):
            # Mock return value
            mock_analyze.return_value = {
                "presidio_available": True,
                "total_detections": 2,
                "entities_found": {"PERSON": ["John Doe"]},
                "confidence_scores": [0.9, 0.8],
                "sample_analyzed": 3,
            }

            results = processor._analyze_chunk_text_content(chunk, text_columns, config)

            # Should analyze each text column
            assert mock_analyze.call_count == len(text_columns)

            # Should return results for columns with detections
            assert isinstance(results, dict)

    def test_aggregate_chunk_results(self):
        """Test aggregation of results from multiple chunks."""
        processor = BatchPIIProcessor()

        # Mock chunk results
        chunk_results = {
            "email_col": [
                {
                    "total_detections": 3,
                    "sample_analyzed": 10,
                    "confidence_scores": [0.9, 0.8, 0.7],
                    "entities_found": {"EMAIL_ADDRESS": ["email1", "email2", "email3"]},
                },
                {
                    "total_detections": 2,
                    "sample_analyzed": 8,
                    "confidence_scores": [0.85, 0.75],
                    "entities_found": {"EMAIL_ADDRESS": ["email4", "email5"]},
                },
            ],
            "phone_col": [
                {
                    "total_detections": 1,
                    "sample_analyzed": 5,
                    "confidence_scores": [0.6],  # Below default threshold
                    "entities_found": {"PHONE_NUMBER": ["phone1"]},
                }
            ],
        }

        config = processor._get_optimized_detection_config()
        results = processor._aggregate_chunk_results(chunk_results, config)

        # Should aggregate email_col (above threshold)
        assert "email_col" in results
        email_result = results["email_col"]
        assert isinstance(email_result, PIIDetectionResult)
        assert email_result.detection_method == "presidio_batch_text"
        assert email_result.details["total_detections"] == 5  # 3 + 2
        assert email_result.details["total_samples"] == 18  # 10 + 8

        # Should exclude phone_col (below threshold after aggregation)
        # This depends on the confidence threshold calculation

    def test_anonymize_batch_small_dataset(self):
        """Test batch anonymization on small dataset."""
        processor = BatchPIIProcessor()
        df = self.create_test_dataset(200)

        # Create mock PII results
        pii_results = {
            "name": PIIDetectionResult(
                column_name="name",
                detection_method="column_name_matching",
                confidence=0.9,
            ),
            "email": PIIDetectionResult(
                column_name="email", detection_method="format_patterns", confidence=0.95
            ),
        }

        anonymized_df, report = processor.anonymize_batch(df, pii_results)

        # Should return anonymized dataset and report
        assert isinstance(anonymized_df, pd.DataFrame)
        assert isinstance(report, dict)
        assert anonymized_df.shape == df.shape

        # Should have processed the PII columns differently
        assert not anonymized_df["name"].equals(df["name"])
        assert not anonymized_df["email"].equals(df["email"])

        # Non-PII columns should be unchanged
        assert anonymized_df["age"].equals(df["age"])
        assert anonymized_df["salary"].equals(df["salary"])

    def test_anonymize_batch_large_dataset_chunked(self):
        """Test batch anonymization with chunking."""
        processor = BatchPIIProcessor(chunk_size=100)  # Force chunking
        df = self.create_test_dataset(300)  # Dataset larger than chunk size

        pii_results = {
            "comments": PIIDetectionResult(
                column_name="comments",
                detection_method="presidio_text_analysis",
                confidence=0.8,
                entity_types=["PERSON"],
            )
        }

        progress_calls = []

        def progress_callback(percent, message):
            progress_calls.append((percent, message))

        anonymized_df, report = processor.anonymize_batch(
            df, pii_results, progress_callback=progress_callback
        )

        # Should return results
        assert isinstance(anonymized_df, pd.DataFrame)
        assert isinstance(report, dict)
        assert anonymized_df.shape == df.shape

        # Should have called progress callback multiple times (chunked processing)
        assert len(progress_calls) > 1

        # Report should indicate batch processing
        assert report.get("batch_anonymization") is True
        assert "chunks_processed" in report

    def test_optimized_detection_config(self):
        """Test optimized configuration generation."""
        processor = BatchPIIProcessor(chunk_size=500)
        config = processor._get_optimized_detection_config()

        # Should return configuration dictionary
        assert isinstance(config, dict)

        # Should include batch processing optimizations
        assert "batch_processing" in config
        assert config["batch_processing"] is True

        # Sample size should be related to chunk size
        expected_sample_size = min(200, 500 // 5)  # From implementation
        assert config["presidio_sample_size"] == expected_sample_size

        # Should have slightly lower confidence threshold for batch
        assert config["presidio_confidence_threshold"] == 0.6


class TestPresidioDataFrameFunctions:
    """Test new DataFrame-level Presidio functions."""

    def create_test_dataframe(self):
        """Create test DataFrame with various text columns."""
        return pd.DataFrame(
            {
                "name": ["John Doe", "Jane Smith", "Bob Wilson"],
                "email": ["john@test.com", "jane@test.com", "bob@test.com"],
                "phone": ["555-0123", "555-0456", "555-0789"],
                "comments": [
                    "Contact John at his email",
                    "Jane prefers phone calls at 555-0456",
                    "Bob's address is 123 Main St",
                ],
                "age": [25, 30, 35],
                "score": [85.5, 92.3, 78.1],
            }
        )

    def test_presidio_analyze_dataframe_batch(self):
        """Test batch DataFrame analysis function."""
        df = self.create_test_dataframe()

        # Test with Presidio not available
        with patch(
            "pii_detector.core.presidio_engine.get_presidio_analyzer"
        ) as mock_get_analyzer:
            mock_analyzer = Mock()
            mock_analyzer.is_available.return_value = False
            mock_get_analyzer.return_value = mock_analyzer

            results = presidio_analyze_dataframe_batch(df)
            assert results == {}

    def test_presidio_analyze_dataframe_batch_with_mock(self):
        """Test batch DataFrame analysis with mocked Presidio."""
        df = self.create_test_dataframe()
        text_columns = ["name", "email", "comments"]

        with patch(
            "pii_detector.core.presidio_engine.get_presidio_analyzer"
        ) as mock_get_analyzer:
            mock_analyzer = Mock()
            mock_analyzer.is_available.return_value = True
            mock_analyzer.analyze_column_text.return_value = {
                "total_detections": 2,
                "entities_found": {
                    "PERSON": ["John"],
                    "EMAIL_ADDRESS": ["john@test.com"],
                },
                "confidence_scores": [0.9, 0.8],
            }
            mock_get_analyzer.return_value = mock_analyzer

            results = presidio_analyze_dataframe_batch(
                df, text_columns=text_columns, confidence_threshold=0.7
            )

            # Should analyze specified columns
            assert mock_analyzer.analyze_column_text.call_count == len(text_columns)

            # Should return results for columns with detections
            assert isinstance(results, dict)
            assert len(results) == len(text_columns)  # Mock returns detections for all

    def test_presidio_anonymize_dataframe_batch(self):
        """Test batch DataFrame anonymization function."""
        df = self.create_test_dataframe()
        columns_to_anonymize = ["name", "email"]

        # Test with Presidio not available
        with patch(
            "pii_detector.core.presidio_engine.get_presidio_analyzer"
        ) as mock_get_analyzer:
            mock_analyzer = Mock()
            mock_analyzer.is_available.return_value = False
            mock_get_analyzer.return_value = mock_analyzer

            result_df = presidio_anonymize_dataframe_batch(df, columns_to_anonymize)

            # Should return original DataFrame when Presidio not available
            assert result_df.equals(df)

    def test_presidio_anonymize_dataframe_batch_with_mock(self):
        """Test batch DataFrame anonymization with mocked Presidio."""
        df = self.create_test_dataframe()
        columns_to_anonymize = ["name", "email"]

        with patch(
            "pii_detector.core.presidio_engine.get_presidio_analyzer"
        ) as mock_get_analyzer:
            mock_analyzer = Mock()
            mock_analyzer.is_available.return_value = True
            mock_get_analyzer.return_value = mock_analyzer

            # Mock the anonymize_text method
            with patch(
                "pii_detector.core.presidio_engine.presidio_anonymize_text_column"
            ) as mock_anonymize:
                mock_anonymize.return_value = pd.Series(
                    ["[PERSON]", "[PERSON]", "[PERSON]"]
                )

                result_df = presidio_anonymize_dataframe_batch(df, columns_to_anonymize)

                # Should call anonymization for specified columns
                assert mock_anonymize.call_count == len(columns_to_anonymize)

                # Should return modified DataFrame
                assert isinstance(result_df, pd.DataFrame)
                assert result_df.shape == df.shape


class TestBatchProcessingConvenienceFunctions:
    """Test convenience functions for batch processing."""

    def create_test_dataset(self, size: int = 500) -> pd.DataFrame:
        """Create test dataset."""
        np.random.seed(42)
        return pd.DataFrame(
            {
                "id": range(size),
                "name": [f"Person {i}" for i in range(size)],
                "email": [f"person{i}@test.com" for i in range(size)],
                "phone": [f"555-{i:04d}" for i in range(size)],
                "notes": [f"Note about person {i}" for i in range(size)],
            }
        )

    def test_process_dataset_batch(self):
        """Test complete batch processing workflow."""
        df = self.create_test_dataset(300)

        progress_calls = []

        def progress_callback(percent, message):
            progress_calls.append((percent, message))

        # Mock to avoid external dependencies
        with patch(
            "pii_detector.core.batch_processor.BatchPIIProcessor"
        ) as mock_processor_class:
            mock_processor = Mock()

            # Mock detection results
            mock_detection_results = {
                "name": PIIDetectionResult(
                    column_name="name",
                    detection_method="column_name_matching",
                    confidence=0.9,
                ),
                "email": PIIDetectionResult(
                    column_name="email",
                    detection_method="format_patterns",
                    confidence=0.95,
                ),
            }

            # Mock anonymized dataset and report
            mock_anonymized_df = df.copy()
            mock_anonymized_df["name"] = "[REDACTED]"
            mock_report = {"processed": True, "columns": 2}

            mock_processor.detect_pii_batch.return_value = mock_detection_results
            mock_processor.anonymize_batch.return_value = (
                mock_anonymized_df,
                mock_report,
            )
            mock_processor_class.return_value = mock_processor

            # Test the function
            detection_results, anonymized_df, report = process_dataset_batch(
                df,
                language="en",
                chunk_size=100,
                max_workers=2,
                progress_callback=progress_callback,
            )

            # Verify processor was created with correct parameters
            mock_processor_class.assert_called_once_with(
                language="en", chunk_size=100, max_workers=2
            )

            # Verify methods were called
            mock_processor.detect_pii_batch.assert_called_once()
            mock_processor.anonymize_batch.assert_called_once()

            # Verify results
            assert detection_results == mock_detection_results
            assert anonymized_df.equals(mock_anonymized_df)
            assert report == mock_report

    def test_process_dataset_batch_with_configs(self):
        """Test batch processing with custom configurations."""
        df = self.create_test_dataset(200)

        detection_config = {
            "use_presidio_detection": False,
            "presidio_confidence_threshold": 0.8,
        }

        anonymization_config = {
            "name": {"method": "hash_pseudonymization"},
            "email": {"method": "remove"},
        }

        # Mock processor
        with patch(
            "pii_detector.core.batch_processor.BatchPIIProcessor"
        ) as mock_processor_class:
            mock_processor = Mock()
            mock_processor.detect_pii_batch.return_value = {}
            mock_processor.anonymize_batch.return_value = (df, {})
            mock_processor_class.return_value = mock_processor

            # Test with configs
            detection_results, anonymized_df, report = process_dataset_batch(
                df,
                detection_config=detection_config,
                anonymization_config=anonymization_config,
            )

            # Verify configs were passed to methods
            mock_processor.detect_pii_batch.assert_called_once()
            mock_processor.anonymize_batch.assert_called_once()

            # Extract call arguments
            detection_call_args = mock_processor.detect_pii_batch.call_args
            anonymization_call_args = mock_processor.anonymize_batch.call_args

            # Verify detection config was passed
            assert detection_call_args[0][1] is None  # label_dict
            assert detection_call_args[0][2] == detection_config

            # Verify anonymization config was passed
            assert anonymization_call_args[0][2] == anonymization_config


class TestBatchProcessingEdgeCases:
    """Test edge cases and error handling in batch processing."""

    def test_empty_dataset(self):
        """Test batch processing with empty dataset."""
        empty_df = pd.DataFrame()
        processor = BatchPIIProcessor()

        results = processor.detect_pii_batch(empty_df)
        assert isinstance(results, dict)
        assert len(results) == 0

    def test_single_column_dataset(self):
        """Test batch processing with single column."""
        df = pd.DataFrame({"single_col": ["value1", "value2", "value3"]})
        processor = BatchPIIProcessor()

        results = processor.detect_pii_batch(df)
        assert isinstance(results, dict)

    def test_no_text_columns(self):
        """Test batch processing with no text columns."""
        df = pd.DataFrame(
            {
                "numeric_col": [1, 2, 3, 4, 5],
                "boolean_col": [True, False, True, False, True],
            }
        )
        processor = BatchPIIProcessor()

        results = processor.detect_pii_batch(df)
        assert isinstance(results, dict)
        # Should still run structural analysis

    def test_chunk_size_larger_than_dataset(self):
        """Test when chunk size is larger than dataset."""
        df = pd.DataFrame({"col": ["value1", "value2"]})
        processor = BatchPIIProcessor(chunk_size=1000)  # Much larger than dataset

        results = processor.detect_pii_batch(df)
        assert isinstance(results, dict)

    def test_invalid_progress_callback(self):
        """Test with progress callback that raises exceptions."""
        df = pd.DataFrame({"col": range(100)})
        processor = BatchPIIProcessor()

        def failing_callback(percent, message):
            raise Exception("Callback failed")

        # Should not crash even if callback fails
        results = processor.detect_pii_batch(df, progress_callback=failing_callback)
        assert isinstance(results, dict)


class TestBatchProcessingIntegration:
    """Integration tests for batch processing (may require external dependencies)."""

    @pytest.mark.slow
    def test_batch_vs_standard_consistency(self):
        """Test that batch processing produces consistent results with standard processing."""
        # Create test dataset
        np.random.seed(42)
        df = pd.DataFrame(
            {
                "name": ["John Doe", "Jane Smith", "Bob Wilson"] * 100,
                "email": ["john@test.com", "jane@test.com", "bob@test.com"] * 100,
                "age": np.random.randint(18, 80, 300),
                "notes": ["Some notes about the person"] * 300,
            }
        )

        # Standard processing
        standard_processor = BatchPIIProcessor(chunk_size=10000)  # No chunking
        standard_results = standard_processor.detect_pii_batch(df)

        # Batch processing
        batch_processor = BatchPIIProcessor(chunk_size=100)  # Force chunking
        batch_results = batch_processor.detect_pii_batch(df)

        # Results should be similar (same columns detected)
        standard_columns = set(standard_results.keys())
        batch_columns = set(batch_results.keys())

        # Allow for some differences due to sampling and chunking
        overlap = standard_columns & batch_columns
        total_unique = standard_columns | batch_columns

        if total_unique:  # Only check if any PII was detected
            overlap_ratio = len(overlap) / len(total_unique)
            assert overlap_ratio >= 0.7, (
                f"Batch and standard processing should produce similar results. Overlap: {overlap_ratio}"
            )

    @pytest.mark.skipif(
        True, reason="Requires full Presidio installation - integration test only"
    )
    def test_with_real_presidio(self):
        """Integration test with real Presidio (if available)."""
        df = pd.DataFrame(
            {
                "text": [
                    "Contact John Doe at john.doe@example.com or call 555-123-4567",
                    "Jane Smith lives at 123 Main Street, Springfield, IL 62701",
                    "Bob's SSN is 123-45-6789 and he works at Acme Corp",
                ]
            }
        )

        processor = BatchPIIProcessor()

        # This will only work if Presidio is actually installed
        if processor.presidio_analyzer.is_available():
            results = processor.detect_pii_batch(df)

            # Should detect PII in the text column
            assert "text" in results
            text_result = results["text"]
            assert len(text_result.entity_types) > 0


if __name__ == "__main__":
    pytest.main([__file__])
