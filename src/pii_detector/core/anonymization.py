"""Comprehensive anonymization techniques for PII data.

Based on research from FSD guidelines and academic literature on data anonymization.
Implements various statistical disclosure control methods.
"""

import hashlib
import random
import re
from typing import Any

import numpy as np
import pandas as pd

from pii_detector.core.hash_utils import generate_hash


class AnonymizationTechniques:
    """Collection of anonymization methods for different data types and use cases."""

    def __init__(self, random_seed: int = 42):
        """Initialize with optional random seed for reproducible results."""
        self.random_seed = random_seed
        random.seed(random_seed)
        np.random.seed(random_seed)

    # ==================== REMOVAL TECHNIQUES ====================

    def remove_variables(self, df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
        """Remove entire columns containing PII."""
        return df.drop(columns=columns, errors="ignore")

    def remove_records_with_unique_combinations(
        self, df: pd.DataFrame, columns: list[str], threshold: int = 1
    ) -> pd.DataFrame:
        """Remove records that have unique combinations in specified columns."""
        # Count combinations
        combination_counts = df.groupby(columns).size()
        rare_combinations = combination_counts[combination_counts <= threshold].index

        # Remove records with rare combinations
        mask = ~df.set_index(columns).index.isin(rare_combinations)
        return df[mask].reset_index(drop=True)

    # ==================== PSEUDONYMIZATION TECHNIQUES ====================

    def hash_pseudonymization(
        self, series: pd.Series, consistent: bool = True, prefix: str = ""
    ) -> pd.Series:
        """Replace values with consistent hash-based pseudonyms."""
        if consistent:
            # Use consistent hashing for same values
            return series.apply(
                lambda x: f"{prefix}{generate_hash(str(x))[:8]}" if pd.notna(x) else x
            )
        else:
            # Random pseudonyms (not consistent across same values)
            unique_values = series.dropna().unique()
            pseudonym_map = {
                val: f"{prefix}{hashlib.md5(f'{val}_{random.random()}'.encode()).hexdigest()[:8]}"
                for val in unique_values
            }
            return series.map(pseudonym_map).fillna(series)

    def name_pseudonymization(
        self, series: pd.Series, name_type: str = "generic"
    ) -> pd.Series:
        """Replace names with consistent pseudonyms."""
        name_pools = {
            "generic": ["Person_A", "Person_B", "Person_C", "Person_D", "Person_E"],
            "coded": ["P001", "P002", "P003", "P004", "P005"],
            "alphabetic": ["Alpha", "Beta", "Gamma", "Delta", "Epsilon"],
        }

        pool = name_pools.get(name_type, name_pools["generic"])
        unique_names = series.dropna().unique()

        # Create consistent mapping
        name_map = {}
        for i, name in enumerate(unique_names):
            if i < len(pool):
                name_map[name] = pool[i]
            else:
                # Generate additional names if needed
                name_map[name] = f"{name_type}_{i + 1}"

        return series.map(name_map).fillna(series)

    # ==================== RECODING/CATEGORIZATION TECHNIQUES ====================

    def age_categorization(
        self,
        series: pd.Series,
        bins: list[int] | None = None,
        labels: list[str] | None = None,
    ) -> pd.Series:
        """Convert ages to categories."""
        if bins is None:
            bins = [0, 18, 30, 45, 60, 100]
        if labels is None:
            labels = ["Under 18", "18-29", "30-44", "45-59", "60+"]

        # Handle missing values by converting to numeric first
        numeric_series = pd.to_numeric(series, errors="coerce")
        return pd.cut(numeric_series, bins=bins, labels=labels, include_lowest=True)

    def income_categorization(
        self,
        series: pd.Series,
        bins: list[int] | None = None,
        labels: list[str] | None = None,
    ) -> pd.Series:
        """Convert income to categories."""
        if bins is None:
            bins = [0, 25000, 50000, 75000, 100000, float("inf")]
        if labels is None:
            labels = ["Low", "Lower-Middle", "Middle", "Upper-Middle", "High"]

        return pd.cut(series, bins=bins, labels=labels, include_lowest=True)

    def date_generalization(
        self, series: pd.Series, precision: str = "month"
    ) -> pd.Series:
        """Generalize dates to reduce precision."""
        date_series = pd.to_datetime(series, errors="coerce")

        if precision == "year":
            return date_series.dt.year
        elif precision == "month":
            return date_series.dt.to_period("M")
        elif precision == "quarter":
            return date_series.dt.to_period("Q")
        else:
            return date_series

    def geographic_generalization(
        self, series: pd.Series, level: str = "region"
    ) -> pd.Series:
        """Generalize geographic information."""
        # Mock implementation - in practice would use geographic databases
        geo_mappings = {
            "region": {
                # US States to regions example
                "California": "West",
                "Nevada": "West",
                "Oregon": "West",
                "Texas": "South",
                "Florida": "South",
                "Georgia": "South",
                "New York": "Northeast",
                "Massachusetts": "Northeast",
                "Illinois": "Midwest",
                "Ohio": "Midwest",
            },
            "country": {
                # Cities to countries
                "New York": "USA",
                "Los Angeles": "USA",
                "Chicago": "USA",
                "London": "UK",
                "Manchester": "UK",
                "Paris": "France",
                "Berlin": "Germany",
            },
        }

        mapping = geo_mappings.get(level, {})
        return series.map(mapping).fillna("Other")

    def top_bottom_coding(
        self,
        series: pd.Series,
        top_percentile: float = 95,
        bottom_percentile: float = 5,
    ) -> pd.Series:
        """Apply top and bottom coding to continuous variables."""
        if not pd.api.types.is_numeric_dtype(series):
            return series

        top_threshold = series.quantile(top_percentile / 100)
        bottom_threshold = series.quantile(bottom_percentile / 100)

        result = series.copy()
        result = result.where(result <= top_threshold, f"≥{top_threshold:.0f}")
        # Apply bottom coding only to numeric values
        bottom_mask = pd.to_numeric(result, errors="coerce") >= bottom_threshold
        result = result.where(bottom_mask.fillna(True), f"≤{bottom_threshold:.0f}")

        return result

    # ==================== RANDOMIZATION TECHNIQUES ====================

    def add_noise(
        self, series: pd.Series, noise_type: str = "gaussian", noise_level: float = 0.1
    ) -> pd.Series:
        """Add random noise to numeric data."""
        if not pd.api.types.is_numeric_dtype(series):
            return series

        if noise_type == "gaussian":
            noise = np.random.normal(0, series.std() * noise_level, size=len(series))
        elif noise_type == "uniform":
            noise_range = series.std() * noise_level
            noise = np.random.uniform(-noise_range, noise_range, size=len(series))
        else:
            return series

        return series + noise

    def permutation_swapping(
        self, df: pd.DataFrame, columns: list[str], swap_probability: float = 0.1
    ) -> pd.DataFrame:
        """Randomly swap values between records for specified columns."""
        result_df = df.copy()

        for col in columns:
            if col in df.columns:
                indices = df.index.tolist()
                n_swaps = int(len(indices) * swap_probability)

                for _ in range(n_swaps):
                    # Pick two random indices to swap
                    idx1, idx2 = random.sample(indices, 2)
                    result_df.loc[idx1, col], result_df.loc[idx2, col] = (
                        result_df.loc[idx2, col],
                        result_df.loc[idx1, col],
                    )

        return result_df

    # ==================== STATISTICAL ANONYMIZATION ====================

    def k_anonymity_check(
        self, df: pd.DataFrame, quasi_identifiers: list[str], k: int = 5
    ) -> tuple[bool, pd.DataFrame]:
        """Check if dataset satisfies k-anonymity and return violation groups."""
        if not all(col in df.columns for col in quasi_identifiers):
            raise ValueError("Not all quasi-identifiers found in dataset")

        # Group by quasi-identifiers and count
        groups = df.groupby(quasi_identifiers).size().reset_index(name="count")
        violations = groups[groups["count"] < k]

        is_k_anonymous = len(violations) == 0
        return is_k_anonymous, violations

    def achieve_k_anonymity(
        self, df: pd.DataFrame, quasi_identifiers: list[str], k: int = 5
    ) -> pd.DataFrame:
        """Attempt to achieve k-anonymity through generalization and suppression."""
        result_df = df.copy()

        # Simple approach: remove records that cause violations
        is_anonymous, violations = self.k_anonymity_check(
            result_df, quasi_identifiers, k
        )

        if not is_anonymous:
            # Create a mask for records to keep
            violation_combinations = set()
            for _, row in violations.iterrows():
                combo = tuple(row[col] for col in quasi_identifiers)
                violation_combinations.add(combo)

            # Remove records with violating combinations
            mask = ~result_df[quasi_identifiers].apply(
                lambda row: tuple(row) in violation_combinations, axis=1
            )
            result_df = result_df[mask].reset_index(drop=True)

        return result_df

    # ==================== TEXT ANONYMIZATION ====================

    def text_masking(self, text: str, patterns: dict[str, str] | None = None) -> str:
        """Mask PII patterns in text content."""
        if pd.isna(text) or not isinstance(text, str):
            return text

        if patterns is None:
            patterns = {
                r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b": "[EMAIL]",
                r"\b\d{3}-\d{3}-\d{4}\b": "[PHONE]",
                r"\b\d{3}[-.]?\d{4}\b": "[PHONE]",  # Also catch shorter phone patterns
                r"\b\d{3}[-.]?\d{2}[-.]?\d{4}\b": "[SSN]",
                r"\b\d{1,5}\s+\w+\s+\w+": "[ADDRESS]",
                r"\b[A-Z][a-z]+\s+[A-Z][a-z]+\b": "[NAME]",
            }

        result = text
        for pattern, replacement in patterns.items():
            result = re.sub(pattern, replacement, result)

        return result

    def selective_text_suppression(
        self, text: str, suppress_types: list[str] = None
    ) -> str:
        """Suppress specific types of information from text."""
        if pd.isna(text) or not isinstance(text, str):
            return text

        if suppress_types is None:
            suppress_types = ["names", "locations", "numbers"]

        result = text

        if "names" in suppress_types:
            # Remove proper names (simplified approach)
            result = re.sub(r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b", "[REDACTED]", result)

        if "locations" in suppress_types:
            # Remove location indicators
            location_words = ["street", "avenue", "road", "city", "state", "zip"]
            for word in location_words:
                result = re.sub(
                    rf"\b\w*{word}\w*\b", "[LOCATION]", result, flags=re.IGNORECASE
                )

        if "numbers" in suppress_types:
            # Remove number sequences
            result = re.sub(r"\b\d{3,}\b", "[NUMBER]", result)

        return result

    # ==================== UTILITY METHODS ====================

    def anonymization_report(
        self, original_df: pd.DataFrame, anonymized_df: pd.DataFrame
    ) -> dict[str, Any]:
        """Generate a report comparing original and anonymized datasets."""
        report = {
            "original_rows": len(original_df),
            "anonymized_rows": len(anonymized_df),
            "rows_removed": len(original_df) - len(anonymized_df),
            "removal_percentage": (
                (len(original_df) - len(anonymized_df)) / len(original_df)
            )
            * 100,
            "columns_comparison": {},
            "data_utility_metrics": {},
        }

        # Compare columns
        for col in original_df.columns:
            if col in anonymized_df.columns:
                orig_unique = original_df[col].nunique()
                anon_unique = anonymized_df[col].nunique()

                report["columns_comparison"][col] = {
                    "original_unique_values": orig_unique,
                    "anonymized_unique_values": anon_unique,
                    "uniqueness_reduction": ((orig_unique - anon_unique) / orig_unique)
                    * 100
                    if orig_unique > 0
                    else 0,
                }

        return report


# ==================== MOCK IMPLEMENTATIONS FOR FUTURE FEATURES ====================


class AdvancedAnonymization:
    """Mock implementations for advanced anonymization techniques not yet fully implemented."""

    @staticmethod
    def l_diversity_check(
        df: pd.DataFrame,
        quasi_identifiers: list[str],
        sensitive_attribute: str,
        diversity_l: int = 2,
    ) -> bool:
        """Mock: Check if dataset satisfies l-diversity."""
        # TODO: Implement l-diversity checking
        return False

    @staticmethod
    def t_closeness_check(
        df: pd.DataFrame,
        quasi_identifiers: list[str],
        sensitive_attribute: str,
        t: float = 0.2,
    ) -> bool:
        """Mock: Check if dataset satisfies t-closeness."""
        # TODO: Implement t-closeness checking
        return False

    @staticmethod
    def differential_privacy_noise(
        series: pd.Series, epsilon: float = 1.0
    ) -> pd.Series:
        """Mock: Apply differential privacy noise."""
        # TODO: Implement proper differential privacy
        return series

    @staticmethod
    def synthetic_data_generation(
        df: pd.DataFrame, method: str = "gan"
    ) -> pd.DataFrame:
        """Mock: Generate synthetic data preserving statistical properties."""
        # TODO: Implement synthetic data generation
        return df.copy()
