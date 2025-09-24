"""Tests for the core processor module."""

import pandas as pd
import pytest

from pii_detector.core.processor import (
    clean_column,
    column_is_sparse,
    remove_other_refuse_and_dont_know,
    word_match,
)
from pii_detector.data.constants import FUZZY, STRICT


class TestWordMatch:
    """Test word matching functionality."""

    def test_strict_match_exact(self):
        """Test strict matching with exact match."""
        assert word_match("name", "name", STRICT) is True

    def test_strict_match_case_insensitive(self):
        """Test strict matching is case insensitive."""
        assert word_match("NAME", "name", STRICT) is True
        assert word_match("name", "NAME", STRICT) is True

    def test_strict_match_no_match(self):
        """Test strict matching with no match."""
        assert word_match("first_name", "name", STRICT) is False

    def test_fuzzy_match_contained(self):
        """Test fuzzy matching with contained word."""
        assert word_match("first_name", "name", FUZZY) is True
        assert word_match("lastname", "name", FUZZY) is True

    def test_fuzzy_match_case_insensitive(self):
        """Test fuzzy matching is case insensitive."""
        assert word_match("FIRST_NAME", "name", FUZZY) is True

    def test_fuzzy_match_no_match(self):
        """Test fuzzy matching with no match."""
        assert word_match("age", "name", FUZZY) is False


class TestColumnCleaning:
    """Test column cleaning functionality."""

    def test_remove_other_refuse_and_dont_know(self):
        """Test removal of survey response codes."""
        # Create test series with survey codes
        test_data = pd.Series(["answer1", "999", "-999", "answer2", "777"])
        result = remove_other_refuse_and_dont_know(test_data)

        # Should remove 999, -999, 777 (3-digit repeated numbers)
        expected_values = ["answer1", "answer2"]
        assert list(result) == expected_values

    def test_clean_column_basic(self):
        """Test basic column cleaning."""
        # Create test series with NaN, empty string, and survey codes
        test_data = pd.Series(["valid1", None, "", "999", "valid2", "-777"])
        result = clean_column(test_data)

        # Should keep only valid entries
        expected_values = ["valid1", "valid2"]
        assert list(result) == expected_values

    def test_column_is_sparse_high_sparsity(self):
        """Test sparse column detection with high sparsity."""
        # Create dataset with mostly unique values
        test_df = pd.DataFrame(
            {"sparse_col": ["value1", "value2", "value3", "value4", "value5"]}
        )

        # With threshold 0.8, should be considered sparse (5/5 = 1.0 > 0.8)
        assert column_is_sparse(test_df, "sparse_col", 0.8) is True

    def test_column_is_sparse_low_sparsity(self):
        """Test sparse column detection with low sparsity."""
        # Create dataset with repeated values
        test_df = pd.DataFrame(
            {"dense_col": ["value1", "value1", "value1", "value2", "value2"]}
        )

        # With threshold 0.8, should not be considered sparse (2/5 = 0.4 < 0.8)
        assert column_is_sparse(test_df, "dense_col", 0.8) is False


class TestImportDataset:
    """Test dataset import functionality."""

    def test_unsupported_file_format(self):
        """Test handling of unsupported file formats."""
        from pii_detector.core.processor import import_dataset

        success, result = import_dataset("test.txt")
        assert success is False
        assert "Supported files are" in result


# Integration test example
@pytest.mark.integration
def test_basic_workflow():
    """Test basic PII detection workflow."""
    # Create a simple test dataset
    test_df = pd.DataFrame(
        {
            "name": ["John Doe", "Jane Smith", "Bob Johnson"],
            "age": [25, 30, 35],
            "email": ["john@email.com", "jane@email.com", "bob@email.com"],
            "id": [1, 2, 3],
        }
    )

    # Test that we can identify sparse columns
    # Email column should be considered sparse (all unique values)
    assert column_is_sparse(test_df, "email", 0.5) is True

    # Age column should not be sparse with this data
    assert (
        column_is_sparse(test_df, "age", 0.5) is True
    )  # Actually sparse in this small example

    # Name column should be sparse (all unique)
    assert column_is_sparse(test_df, "name", 0.5) is True


if __name__ == "__main__":
    pytest.main([__file__])
