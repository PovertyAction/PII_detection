"""
Pytest configuration and fixtures for PII detector tests.
"""

from unittest.mock import Mock

import numpy as np
import pandas as pd
import pytest


@pytest.fixture
def sample_dataset():
    """Create a sample dataset for testing."""
    np.random.seed(42)
    return pd.DataFrame(
        {
            "id": range(1, 11),
            "name": [
                "John Doe",
                "Jane Smith",
                "Bob Wilson",
                "Alice Brown",
                "Charlie Davis",
                "Diana Evans",
                "Frank Miller",
                "Grace Lee",
                "Henry Taylor",
                "Ivy Chen",
            ],
            "email": [f"person{i}@test.com" for i in range(10)],
            "phone": [f"555-{i:04d}" for i in range(10)],
            "age": np.random.randint(18, 80, 10),
            "notes": [f"Note about person {i}" for i in range(10)],
        }
    )


@pytest.fixture
def large_sample_dataset():
    """Create a larger sample dataset for batch processing tests."""
    np.random.seed(42)
    size = 1000

    return pd.DataFrame(
        {
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
    )


@pytest.fixture
def text_heavy_dataset():
    """Create a dataset with lots of text content for Presidio testing."""
    return pd.DataFrame(
        {
            "participant_id": range(1, 6),
            "full_name": [
                "John Doe",
                "Jane Smith",
                "Bob Wilson",
                "Alice Brown",
                "Charlie Davis",
            ],
            "contact_info": [
                "Email: john.doe@example.com, Phone: 555-123-4567",
                "Reach Jane at jane.smith@test.org or call 555-987-6543",
                "Bob Wilson can be contacted at bob@company.com",
                "Alice's number is 555-111-2222 and email alice.brown@email.com",
                "Charlie Davis, charlie.davis@workplace.net, office: 555-444-5555",
            ],
            "address_info": [
                "123 Main Street, Springfield, IL 62701",
                "456 Oak Avenue, Chicago, IL 60601",
                "789 Pine Road, Peoria, IL 61602",
                "321 Elm Street, Rockford, IL 61103",
                "654 Maple Drive, Naperville, IL 60540",
            ],
            "personal_notes": [
                "John mentioned his SSN is 123-45-6789 for verification",
                "Jane's driver license number is D123456789",
                "Bob shared his credit card info: 4532-1234-5678-9012",
                "Alice provided her passport number: A12345678",
                "Charlie's bank account: 987654321 at First National Bank",
            ],
        }
    )


@pytest.fixture
def mock_presidio_analyzer():
    """Create a mock Presidio analyzer for testing."""
    mock_analyzer = Mock()
    mock_analyzer.is_available.return_value = True
    mock_analyzer.language = "en"

    # Mock analysis results
    mock_analyzer.analyze_text.return_value = [
        {
            "entity_type": "PERSON",
            "start": 0,
            "end": 8,
            "score": 0.9,
            "text": "John Doe",
        }
    ]

    # Mock column analysis results
    mock_analyzer.analyze_column_text.return_value = {
        "presidio_available": True,
        "entities_found": {"PERSON": [{"text": "John Doe", "score": 0.9}]},
        "total_detections": 1,
        "confidence_scores": [0.9],
        "sample_analyzed": 10,
        "average_confidence": 0.9,
    }

    # Mock anonymization
    mock_analyzer.anonymize_text.return_value = "[PERSON]"

    return mock_analyzer


@pytest.fixture
def mock_batch_processor():
    """Create a mock batch processor for testing."""
    from pii_detector.core.unified_processor import PIIDetectionResult

    mock_processor = Mock()

    # Mock detection results
    mock_detection_results = {
        "name": PIIDetectionResult(
            column_name="name",
            detection_method="column_name_matching",
            confidence=0.9,
            entity_types=["PERSON"],
        ),
        "email": PIIDetectionResult(
            column_name="email",
            detection_method="format_patterns",
            confidence=0.95,
            entity_types=["EMAIL_ADDRESS"],
        ),
    }

    mock_processor.detect_pii_batch.return_value = mock_detection_results

    # Mock anonymization results
    def mock_anonymize_batch(df, pii_results, config=None, callback=None):
        anonymized_df = df.copy()
        for col in pii_results:
            if col in anonymized_df.columns:
                anonymized_df[col] = "[REDACTED]"

        report = {
            "original_shape": df.shape,
            "final_shape": anonymized_df.shape,
            "columns_processed": list(pii_results.keys()),
            "batch_processing": True,
        }

        return anonymized_df, report

    mock_processor.anonymize_batch.side_effect = mock_anonymize_batch

    return mock_processor


@pytest.fixture
def detection_config():
    """Standard detection configuration for tests."""
    return {
        "use_column_name_detection": True,
        "use_format_detection": True,
        "use_sparsity_detection": False,  # Disabled for consistent testing
        "use_location_detection": False,  # Disabled to avoid external API calls
        "use_presidio_detection": False,  # Disabled by default for unit tests
        "column_name_confidence": 0.8,
        "format_pattern_confidence": 0.9,
        "presidio_confidence_threshold": 0.7,
        "presidio_sample_size": 50,
    }


@pytest.fixture
def anonymization_config():
    """Standard anonymization configuration for tests."""
    return {
        "consistent_hashing": True,
        "age_bins": [0, 18, 30, 45, 60, 100],
        "age_labels": ["Under 18", "18-29", "30-44", "45-59", "60+"],
        "geo_level": "region",
        "date_precision": "month",
    }


# Pytest markers
pytest_plugins = []


def pytest_configure(config):
    """Configure custom pytest markers."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line("markers", "integration: marks tests as integration tests")
    config.addinivalue_line(
        "markers", "presidio: marks tests that require Presidio installation"
    )
    config.addinivalue_line(
        "markers", "batch: marks tests for batch processing functionality"
    )
