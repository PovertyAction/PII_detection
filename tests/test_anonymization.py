"""
Comprehensive tests for anonymization techniques.

Tests various PII removal and anonymization methods based on FSD guidelines
and academic literature on statistical disclosure control.
"""

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from pii_detector.core.anonymization import (
    AdvancedAnonymization,
    AnonymizationTechniques,
)


class TestAnonymizationTechniques:
    """Test suite for anonymization methods."""

    @pytest.fixture
    def anonymizer(self):
        """Create anonymization techniques instance with fixed seed."""
        return AnonymizationTechniques(random_seed=42)

    @pytest.fixture
    def test_data_dir(self):
        """Get path to test data directory."""
        return Path(__file__).parent / "data"

    @pytest.fixture
    def comprehensive_data(self, test_data_dir):
        """Load comprehensive PII test dataset."""
        return pd.read_csv(test_data_dir / "comprehensive_pii_data.csv")

    @pytest.fixture
    def qualitative_data(self, test_data_dir):
        """Load qualitative data with text content."""
        return pd.read_csv(test_data_dir / "qualitative_data.csv")

    @pytest.fixture
    def sample_numeric_data(self):
        """Create sample numeric data for testing."""
        return pd.DataFrame(
            {
                "age": [25, 30, 45, 60, 35, 28, 50, 40],
                "income": [45000, 65000, 85000, 120000, 55000, 48000, 95000, 72000],
                "score": [85.5, 92.3, 78.1, 88.9, 91.2, 76.8, 89.4, 83.7],
            }
        )

    # ==================== REMOVAL TECHNIQUES TESTS ====================

    def test_remove_variables(self, anonymizer, comprehensive_data):
        """Test complete variable removal."""
        columns_to_remove = ["first_name", "last_name", "ssn", "email"]
        result = anonymizer.remove_variables(comprehensive_data, columns_to_remove)

        # Check that specified columns are removed
        for col in columns_to_remove:
            assert col not in result.columns

        # Check that other columns remain
        assert "age" in result.columns
        assert "city" in result.columns
        assert len(result) == len(comprehensive_data)  # Same number of rows

    def test_remove_records_with_unique_combinations(self, anonymizer):
        """Test removal of records with unique quasi-identifier combinations."""
        # Create test data with some unique combinations
        test_df = pd.DataFrame(
            {
                "age_group": ["20-30", "30-40", "20-30", "40-50", "20-30"],
                "occupation": [
                    "Engineer",
                    "Teacher",
                    "Engineer",
                    "Unique_Job",
                    "Engineer",
                ],
                "city": ["Chicago", "NYC", "Chicago", "SmallTown", "Chicago"],
                "sensitive_data": ["A", "B", "C", "D", "E"],
            }
        )

        result = anonymizer.remove_records_with_unique_combinations(
            test_df, ["age_group", "occupation", "city"], threshold=1
        )

        # Should remove records with unique combinations
        assert len(result) < len(test_df)
        # Records with repeated combinations should remain
        remaining_combinations = result.groupby(
            ["age_group", "occupation", "city"]
        ).size()
        assert all(remaining_combinations > 1)

    # ==================== PSEUDONYMIZATION TESTS ====================

    def test_hash_pseudonymization(self, anonymizer, comprehensive_data):
        """Test hash-based pseudonymization."""
        original_names = comprehensive_data["first_name"]
        pseudonyms = anonymizer.hash_pseudonymization(original_names, prefix="ANON_")

        # Check that values are different but consistent
        assert not pseudonyms.equals(original_names)
        assert all(
            pseudo.startswith("ANON_") for pseudo in pseudonyms if pd.notna(pseudo)
        )

        # Test consistency - same inputs should give same outputs
        pseudonyms2 = anonymizer.hash_pseudonymization(original_names, prefix="ANON_")
        assert pseudonyms.equals(pseudonyms2)

    def test_name_pseudonymization(self, anonymizer, comprehensive_data):
        """Test name-specific pseudonymization."""
        original_names = comprehensive_data["first_name"]

        # Test different name types
        for name_type in ["generic", "coded", "alphabetic"]:
            pseudonyms = anonymizer.name_pseudonymization(original_names, name_type)

            assert not pseudonyms.equals(original_names)
            assert len(pseudonyms) == len(original_names)

            # Check that unique names get consistent pseudonyms
            unique_mapping = dict(zip(original_names.dropna(), pseudonyms.dropna()))
            assert len(unique_mapping) == len(original_names.dropna().unique())

    # ==================== RECODING/CATEGORIZATION TESTS ====================

    def test_age_categorization(self, anonymizer, comprehensive_data):
        """Test age categorization."""
        ages = comprehensive_data["age"]
        categories = anonymizer.age_categorization(ages)

        # Check that ages are converted to categories
        assert categories.dtype.name == "category"
        assert all(
            cat in ["Under 18", "18-29", "30-44", "45-59", "60+"]
            for cat in categories.dropna()
        )

        # Test custom bins
        custom_bins = [0, 25, 35, 50, 100]
        custom_labels = ["Young", "Adult", "Middle", "Senior"]
        custom_categories = anonymizer.age_categorization(
            ages, custom_bins, custom_labels
        )
        assert all(cat in custom_labels for cat in custom_categories.dropna())

    def test_income_categorization(self, anonymizer, comprehensive_data):
        """Test income categorization."""
        incomes = comprehensive_data["income"]
        categories = anonymizer.income_categorization(incomes)

        assert categories.dtype.name == "category"
        expected_categories = ["Low", "Lower-Middle", "Middle", "Upper-Middle", "High"]
        assert all(cat in expected_categories for cat in categories.dropna())

    def test_date_generalization(self, anonymizer, comprehensive_data):
        """Test date generalization to different precision levels."""
        dates = comprehensive_data["date_of_birth"]

        # Test year precision
        years = anonymizer.date_generalization(dates, precision="year")
        assert all(isinstance(year, (int, np.integer)) for year in years.dropna())

        # Test month precision
        months = anonymizer.date_generalization(dates, precision="month")
        assert all(hasattr(month, "year") for month in months.dropna())

        # Test quarter precision
        quarters = anonymizer.date_generalization(dates, precision="quarter")
        assert all(hasattr(quarter, "year") for quarter in quarters.dropna())

    def test_geographic_generalization(self, anonymizer, comprehensive_data):
        """Test geographic generalization."""
        states = comprehensive_data["state"]

        # Test region mapping
        regions = anonymizer.geographic_generalization(states, level="region")
        # Should have fewer unique values than original
        assert regions.nunique() <= states.nunique()

    def test_top_bottom_coding(self, anonymizer, sample_numeric_data):
        """Test top and bottom coding of continuous variables."""
        incomes = sample_numeric_data["income"]
        coded_incomes = anonymizer.top_bottom_coding(
            incomes, top_percentile=90, bottom_percentile=10
        )

        # Should have some string values for extreme values
        assert any(isinstance(val, str) for val in coded_incomes)
        # Should contain ≥ or ≤ symbols
        string_values = [val for val in coded_incomes if isinstance(val, str)]
        assert any("≥" in str(val) or "≤" in str(val) for val in string_values)

    # ==================== RANDOMIZATION TESTS ====================

    def test_add_noise(self, anonymizer, sample_numeric_data):
        """Test noise addition to numeric data."""
        original_scores = sample_numeric_data["score"]

        # Test Gaussian noise
        noisy_scores_gaussian = anonymizer.add_noise(
            original_scores, noise_type="gaussian", noise_level=0.1
        )
        assert not noisy_scores_gaussian.equals(original_scores)
        assert len(noisy_scores_gaussian) == len(original_scores)

        # Test uniform noise
        noisy_scores_uniform = anonymizer.add_noise(
            original_scores, noise_type="uniform", noise_level=0.1
        )
        assert not noisy_scores_uniform.equals(original_scores)

        # Test that noise doesn't affect non-numeric data
        text_series = pd.Series(["a", "b", "c"])
        text_with_noise = anonymizer.add_noise(text_series)
        assert text_with_noise.equals(text_series)

    def test_permutation_swapping(self, anonymizer, comprehensive_data):
        """Test permutation-based value swapping."""
        original_df = comprehensive_data.copy()
        swapped_df = anonymizer.permutation_swapping(
            original_df, ["age", "income"], swap_probability=0.3
        )

        # DataFrames should have same shape
        assert swapped_df.shape == original_df.shape

        # Some values should be different due to swapping
        age_changes = (swapped_df["age"] != original_df["age"]).sum()
        income_changes = (swapped_df["income"] != original_df["income"]).sum()

        # At least some swapping should have occurred
        assert age_changes > 0 or income_changes > 0

        # Total values should be preserved (just rearranged)
        assert set(swapped_df["age"]) == set(original_df["age"])
        assert set(swapped_df["income"]) == set(original_df["income"])

    # ==================== STATISTICAL ANONYMIZATION TESTS ====================

    def test_k_anonymity_check(self, anonymizer):
        """Test k-anonymity checking."""
        # Create test data that violates k-anonymity
        test_df = pd.DataFrame(
            {
                "age_group": [
                    "20-30",
                    "20-30",
                    "30-40",
                    "40-50",
                ],  # One unique combination
                "occupation": ["Engineer", "Engineer", "Teacher", "UniqueJob"],
                "salary": [50000, 55000, 60000, 100000],
            }
        )

        is_anonymous, violations = anonymizer.k_anonymity_check(
            test_df, ["age_group", "occupation"], k=2
        )

        assert not is_anonymous  # Should violate k-anonymity
        assert len(violations) > 0  # Should have violations
        assert any(violations["count"] < 2)  # Some groups have count < k

    def test_achieve_k_anonymity(self, anonymizer):
        """Test achieving k-anonymity through record removal."""
        # Create test data with k-anonymity violations
        test_df = pd.DataFrame(
            {
                "age_group": ["20-30", "20-30", "20-30", "30-40", "40-50"],
                "education": ["BS", "BS", "MS", "PhD", "HS"],
                "sensitive": ["A", "B", "C", "D", "E"],
            }
        )

        anonymized_df = anonymizer.achieve_k_anonymity(
            test_df, ["age_group", "education"], k=2
        )

        # Check that result satisfies k-anonymity
        is_anonymous, _ = anonymizer.k_anonymity_check(
            anonymized_df, ["age_group", "education"], k=2
        )
        assert is_anonymous

        # Should have fewer or equal rows
        assert len(anonymized_df) <= len(test_df)

    # ==================== TEXT ANONYMIZATION TESTS ====================

    def test_text_masking(self, anonymizer, qualitative_data):
        """Test PII pattern masking in text."""
        sample_text = qualitative_data["interview_transcript"].iloc[0]
        masked_text = anonymizer.text_masking(sample_text)

        # Should replace emails with [EMAIL]
        assert "[EMAIL]" in masked_text
        # Should replace phone numbers with [PHONE]
        assert "[PHONE]" in masked_text
        # Original PII should be removed
        assert "john@abc.com" not in masked_text
        assert "555-1234" not in masked_text

    def test_selective_text_suppression(self, anonymizer, qualitative_data):
        """Test selective suppression of text content."""
        sample_text = qualitative_data["interview_transcript"].iloc[0]

        # Test name suppression
        names_suppressed = anonymizer.selective_text_suppression(
            sample_text, suppress_types=["names"]
        )
        assert "[REDACTED]" in names_suppressed

        # Test location suppression
        locations_suppressed = anonymizer.selective_text_suppression(
            sample_text, suppress_types=["locations"]
        )
        assert "[LOCATION]" in locations_suppressed

        # Test number suppression
        numbers_suppressed = anonymizer.selective_text_suppression(
            sample_text, suppress_types=["numbers"]
        )
        assert "[NUMBER]" in numbers_suppressed

    def test_custom_text_patterns(self, anonymizer):
        """Test custom pattern masking."""
        text = "My SSN is 123-45-6789 and credit card is 4532-1234-5678-9012"
        custom_patterns = {
            r"\b\d{3}-\d{2}-\d{4}\b": "[SSN_MASKED]",
            r"\b\d{4}-\d{4}-\d{4}-\d{4}\b": "[CREDIT_CARD]",
        }

        masked = anonymizer.text_masking(text, patterns=custom_patterns)
        assert "[SSN_MASKED]" in masked
        assert "[CREDIT_CARD]" in masked
        assert "123-45-6789" not in masked
        assert "4532-1234-5678-9012" not in masked

    # ==================== UTILITY TESTS ====================

    def test_anonymization_report(self, anonymizer, comprehensive_data):
        """Test anonymization reporting functionality."""
        # Apply some anonymization
        anonymized = anonymizer.remove_variables(
            comprehensive_data, ["first_name", "last_name"]
        )
        anonymized = anonymized.iloc[:-2]  # Remove some rows too

        report = anonymizer.anonymization_report(comprehensive_data, anonymized)

        # Check report structure
        assert "original_rows" in report
        assert "anonymized_rows" in report
        assert "rows_removed" in report
        assert "removal_percentage" in report
        assert "columns_comparison" in report

        # Check values
        assert report["original_rows"] == len(comprehensive_data)
        assert report["anonymized_rows"] == len(anonymized)
        assert report["rows_removed"] == 2  # We removed 2 rows
        assert report["removal_percentage"] == (2 / len(comprehensive_data)) * 100

    # ==================== EDGE CASES AND ERROR HANDLING ====================

    def test_empty_data_handling(self, anonymizer):
        """Test handling of empty datasets."""
        empty_df = pd.DataFrame()

        # Should not crash on empty data
        result = anonymizer.remove_variables(empty_df, ["nonexistent"])
        assert len(result) == 0

        empty_series = pd.Series(dtype="object")
        result_series = anonymizer.hash_pseudonymization(empty_series)
        assert len(result_series) == 0

    def test_missing_values_handling(self, anonymizer):
        """Test handling of missing values."""
        series_with_na = pd.Series(["John", None, "Jane", pd.NA, "Bob"])

        # Pseudonymization should preserve NaN values
        pseudonyms = anonymizer.hash_pseudonymization(series_with_na)
        assert pseudonyms.isna().sum() == series_with_na.isna().sum()

        # Age categorization should handle NaN
        ages_with_na = pd.Series([25, None, 35, pd.NA, 45])
        categories = anonymizer.age_categorization(ages_with_na)
        assert categories.isna().sum() == ages_with_na.isna().sum()

    def test_non_numeric_noise_addition(self, anonymizer):
        """Test that noise addition doesn't affect non-numeric data."""
        text_data = pd.Series(["apple", "banana", "cherry"])
        result = anonymizer.add_noise(text_data)
        assert result.equals(text_data)

    def test_invalid_column_removal(self, anonymizer, comprehensive_data):
        """Test removal of non-existent columns."""
        # Should not crash when removing non-existent columns
        result = anonymizer.remove_variables(comprehensive_data, ["nonexistent_column"])
        assert result.equals(comprehensive_data)

    # ==================== INTEGRATION TESTS ====================

    @pytest.mark.integration
    def test_full_anonymization_workflow(self, anonymizer, comprehensive_data):
        """Test complete anonymization workflow."""
        original_data = comprehensive_data.copy()

        # Step 1: Remove direct identifiers
        step1 = anonymizer.remove_variables(
            original_data, ["first_name", "last_name", "ssn", "email"]
        )

        # Step 2: Pseudonymize remaining identifiers
        step2 = step1.copy()
        step2["participant_id"] = anonymizer.hash_pseudonymization(
            step1["participant_id"], prefix="P_"
        )

        # Step 3: Categorize continuous variables
        step3 = step2.copy()
        step3["age_group"] = anonymizer.age_categorization(step2["age"])
        step3["income_bracket"] = anonymizer.income_categorization(step2["income"])

        # Step 4: Generalize geography
        step4 = step3.copy()
        step4["region"] = anonymizer.geographic_generalization(step3["state"])

        # Step 5: Apply k-anonymity
        final_result = anonymizer.achieve_k_anonymity(
            step4, ["age_group", "occupation", "region"], k=2
        )

        # Verify transformations
        assert "first_name" not in final_result.columns
        assert "ssn" not in final_result.columns
        assert all(pid.startswith("P_") for pid in final_result["participant_id"])
        assert final_result["age_group"].dtype.name == "category"

        # Generate report
        report = anonymizer.anonymization_report(original_data, final_result)
        assert report["original_rows"] >= report["anonymized_rows"]


class TestAdvancedAnonymization:
    """Test suite for advanced (mock) anonymization techniques."""

    def test_l_diversity_check_mock(self):
        """Test l-diversity mock implementation."""
        df = pd.DataFrame({"quasi": [1, 2, 3], "sensitive": ["A", "B", "C"]})
        result = AdvancedAnonymization.l_diversity_check(
            df, ["quasi"], "sensitive", diversity_l=2
        )
        # Mock should return False
        assert result is False

    def test_t_closeness_check_mock(self):
        """Test t-closeness mock implementation."""
        df = pd.DataFrame({"quasi": [1, 2, 3], "sensitive": ["A", "B", "C"]})
        result = AdvancedAnonymization.t_closeness_check(
            df, ["quasi"], "sensitive", t=0.2
        )
        # Mock should return False
        assert result is False

    def test_differential_privacy_mock(self):
        """Test differential privacy mock implementation."""
        series = pd.Series([1, 2, 3, 4, 5])
        result = AdvancedAnonymization.differential_privacy_noise(series, epsilon=1.0)
        # Mock should return original series
        assert result.equals(series)

    def test_synthetic_data_generation_mock(self):
        """Test synthetic data generation mock."""
        df = pd.DataFrame({"a": [1, 2, 3], "b": ["x", "y", "z"]})
        result = AdvancedAnonymization.synthetic_data_generation(df)
        # Mock should return copy of original
        assert result.equals(df)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
