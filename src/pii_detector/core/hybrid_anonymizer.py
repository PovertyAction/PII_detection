"""Hybrid anonymization engine combining existing techniques with Presidio operators.

This module extends the current anonymization capabilities by integrating Presidio's
advanced text anonymization while preserving all existing statistical anonymization methods.
"""

import logging
from typing import Any

import pandas as pd

from pii_detector.core.anonymization import AnonymizationTechniques
from pii_detector.core.presidio_engine import get_presidio_analyzer
from pii_detector.core.unified_processor import PIIDetectionResult

logger = logging.getLogger(__name__)


class HybridAnonymizer:
    """Hybrid anonymizer combining statistical methods with Presidio text anonymization."""

    def __init__(self, random_seed: int = 42, language: str = "en"):
        """Initialize the hybrid anonymizer.

        Args:
            random_seed: Random seed for reproducible results
            language: Language code for text processing

        """
        self.current_techniques = AnonymizationTechniques(random_seed=random_seed)
        self.presidio_analyzer = get_presidio_analyzer(language=language)
        self.language = language

    def anonymize_dataset(
        self,
        dataset: pd.DataFrame,
        pii_columns: list[str] | dict[str, PIIDetectionResult],
        anonymization_config: dict[str, Any] | None = None,
    ) -> tuple[pd.DataFrame, dict[str, Any]]:
        """Anonymize a dataset using hybrid approach.

        Args:
            dataset: Original dataset
            pii_columns: Either list of column names or detection results
            anonymization_config: Configuration for anonymization methods

        Returns:
            Tuple of (anonymized_dataset, anonymization_report)

        """
        if anonymization_config is None:
            anonymization_config = self._get_default_anonymization_config()

        logger.info(f"Starting hybrid anonymization of {len(dataset)} rows")

        # Convert pii_columns to consistent format
        if isinstance(pii_columns, dict):
            column_detection_map = pii_columns
            column_names = list(pii_columns.keys())
        else:
            column_names = pii_columns
            column_detection_map = {}

        anonymized_dataset = dataset.copy()
        anonymization_log = {
            "original_shape": dataset.shape,
            "columns_processed": [],
            "methods_applied": {},
            "text_anonymization": {},
            "structural_anonymization": {},
        }

        # Process each PII column
        for column_name in column_names:
            if column_name not in dataset.columns:
                logger.warning(f"Column {column_name} not found in dataset")
                continue

            detection_result = column_detection_map.get(column_name)
            column_config = anonymization_config.get(column_name, {})

            # Determine anonymization method
            method = self._determine_anonymization_method(
                dataset[column_name], detection_result, column_config
            )

            logger.info(f"Anonymizing column {column_name} using method: {method}")

            try:
                # Apply anonymization
                anonymized_column, method_log = self._anonymize_column(
                    dataset[column_name], method, detection_result, column_config
                )

                anonymized_dataset[column_name] = anonymized_column

                # Log the results
                anonymization_log["columns_processed"].append(column_name)
                anonymization_log["methods_applied"][column_name] = method

                if method.startswith("presidio"):
                    anonymization_log["text_anonymization"][column_name] = method_log
                else:
                    anonymization_log["structural_anonymization"][column_name] = (
                        method_log
                    )

            except Exception as e:
                logger.error(f"Error anonymizing column {column_name}: {e}")
                # Keep original column if anonymization fails
                anonymization_log["methods_applied"][column_name] = "failed"

        # Generate comprehensive report
        anonymization_report = self.current_techniques.anonymization_report(
            dataset, anonymized_dataset
        )
        anonymization_report.update(anonymization_log)

        logger.info(
            f"Anonymization completed. Processed {len(anonymization_log['columns_processed'])} columns"
        )
        return anonymized_dataset, anonymization_report

    def _determine_anonymization_method(
        self,
        column_data: pd.Series,
        detection_result: PIIDetectionResult | None,
        column_config: dict[str, Any],
    ) -> str:
        """Determine the best anonymization method for a column."""
        # Check if user specified a method
        if "method" in column_config:
            return column_config["method"]

        # If no detection result, use basic removal
        if detection_result is None:
            return "remove"

        # Decide based on detection method and entity types
        detection_method = detection_result.detection_method
        entity_types = detection_result.entity_types

        # Use Presidio for text-based detections with specific entity types
        if (
            detection_method in ["presidio_text_analysis", "hybrid_detection"]
            and entity_types
            and self.presidio_analyzer.is_available()
        ):
            # Check if we have known entity types that Presidio handles well
            presidio_entities = {
                "PERSON",
                "EMAIL_ADDRESS",
                "PHONE_NUMBER",
                "US_SSN",
                "LOCATION",
            }
            if any(entity in presidio_entities for entity in entity_types):
                return "presidio_replace"

        # Use structural methods for specific detection types
        if detection_method == "format_patterns":
            return "text_masking"
        elif detection_method == "sparsity_analysis":
            return "hash_pseudonymization"
        elif detection_method == "column_name_matching":
            # Choose based on likely column type
            column_name_lower = detection_result.column_name.lower()
            if any(word in column_name_lower for word in ["age", "birth"]):
                return "age_categorization"
            elif any(
                word in column_name_lower for word in ["income", "salary", "wage"]
            ):
                return "income_categorization"
            elif any(
                word in column_name_lower for word in ["location", "address", "city"]
            ):
                return "geographic_generalization"
            else:
                return "hash_pseudonymization"
        elif detection_method == "location_population":
            return "geographic_generalization"

        # Default method
        return "hash_pseudonymization"

    def _anonymize_column(
        self,
        column_data: pd.Series,
        method: str,
        detection_result: PIIDetectionResult | None,
        column_config: dict[str, Any],
    ) -> tuple[pd.Series, dict[str, Any]]:
        """Anonymize a single column using the specified method."""
        method_log = {"method": method, "original_unique": column_data.nunique()}

        if method == "remove":
            # Complete removal
            anonymized_data = pd.Series(
                [None] * len(column_data), name=column_data.name
            )
            method_log["action"] = "column_removed"

        elif method == "presidio_replace":
            # Use Presidio for text anonymization
            anonymized_data = self._presidio_anonymize_column(
                column_data, detection_result, column_config
            )
            method_log["presidio_available"] = self.presidio_analyzer.is_available()
            method_log["entity_types"] = (
                detection_result.entity_types if detection_result else []
            )

        elif method == "text_masking":
            # Use current text masking
            anonymized_data = column_data.apply(
                lambda x: self.current_techniques.text_masking(x) if pd.notna(x) else x
            )
            method_log["action"] = "text_patterns_masked"

        elif method == "hash_pseudonymization":
            # Use hash-based pseudonymization
            anonymized_data = self.current_techniques.hash_pseudonymization(
                column_data,
                consistent=column_config.get("consistent_hashing", True),
                prefix=column_config.get("prefix", "ID_"),
            )
            method_log["action"] = "hash_pseudonymization"

        elif method == "age_categorization":
            # Age categorization
            anonymized_data = self.current_techniques.age_categorization(
                column_data,
                bins=column_config.get("age_bins"),
                labels=column_config.get("age_labels"),
            )
            method_log["action"] = "age_categorized"

        elif method == "income_categorization":
            # Income categorization
            anonymized_data = self.current_techniques.income_categorization(
                column_data,
                bins=column_config.get("income_bins"),
                labels=column_config.get("income_labels"),
            )
            method_log["action"] = "income_categorized"

        elif method == "geographic_generalization":
            # Geographic generalization
            anonymized_data = self.current_techniques.geographic_generalization(
                column_data, level=column_config.get("geo_level", "region")
            )
            method_log["action"] = "geography_generalized"

        elif method == "date_generalization":
            # Date generalization
            anonymized_data = self.current_techniques.date_generalization(
                column_data, precision=column_config.get("date_precision", "month")
            )
            method_log["action"] = "dates_generalized"

        elif method == "top_bottom_coding":
            # Top/bottom coding for numeric data
            anonymized_data = self.current_techniques.top_bottom_coding(
                column_data,
                top_percentile=column_config.get("top_percentile", 95),
                bottom_percentile=column_config.get("bottom_percentile", 5),
            )
            method_log["action"] = "top_bottom_coded"

        elif method == "add_noise":
            # Add statistical noise
            anonymized_data = self.current_techniques.add_noise(
                column_data,
                noise_type=column_config.get("noise_type", "gaussian"),
                noise_level=column_config.get("noise_level", 0.1),
            )
            method_log["action"] = "noise_added"

        else:
            # Unknown method - default to hash pseudonymization
            logger.warning(
                f"Unknown anonymization method: {method}. Using hash pseudonymization."
            )
            anonymized_data = self.current_techniques.hash_pseudonymization(column_data)
            method_log["action"] = "default_hash_pseudonymization"
            method_log["warning"] = f"Unknown method {method}"

        method_log["final_unique"] = anonymized_data.nunique()
        method_log["uniqueness_reduction"] = (
            (method_log["original_unique"] - method_log["final_unique"])
            / method_log["original_unique"]
            * 100
            if method_log["original_unique"] > 0
            else 0
        )

        return anonymized_data, method_log

    def _presidio_anonymize_column(
        self,
        column_data: pd.Series,
        detection_result: PIIDetectionResult | None,
        column_config: dict[str, Any],
    ) -> pd.Series:
        """Anonymize column using Presidio text anonymization."""
        if not self.presidio_analyzer.is_available():
            logger.warning("Presidio not available, falling back to text masking")
            return column_data.apply(
                lambda x: self.current_techniques.text_masking(x) if pd.notna(x) else x
            )

        # Custom operators based on detected entities
        operators = column_config.get("presidio_operators")
        if operators is None and detection_result:
            operators = self._create_operators_for_entities(
                detection_result.entity_types
            )

        def anonymize_text_value(text_value):
            if isinstance(text_value, str) and len(text_value.strip()) > 0:
                return self.presidio_analyzer.anonymize_text(
                    text_value, operators=operators
                )
            return text_value

        return column_data.apply(anonymize_text_value)

    def _create_operators_for_entities(self, entity_types: list[str]) -> dict[str, Any]:
        """Create Presidio operators based on detected entity types."""
        if not self.presidio_analyzer.is_available():
            return {}

        try:
            from presidio_anonymizer.entities import OperatorConfig

            operators = {}
            for entity_type in entity_types:
                if entity_type == "PERSON":
                    operators[entity_type] = OperatorConfig(
                        "replace", {"new_value": "[PERSON]"}
                    )
                elif entity_type == "EMAIL_ADDRESS":
                    operators[entity_type] = OperatorConfig(
                        "replace", {"new_value": "[EMAIL]"}
                    )
                elif entity_type == "PHONE_NUMBER":
                    operators[entity_type] = OperatorConfig(
                        "replace", {"new_value": "[PHONE]"}
                    )
                elif entity_type == "US_SSN":
                    operators[entity_type] = OperatorConfig(
                        "replace", {"new_value": "[SSN]"}
                    )
                elif entity_type == "LOCATION":
                    operators[entity_type] = OperatorConfig(
                        "replace", {"new_value": "[LOCATION]"}
                    )
                elif entity_type == "DATE_TIME":
                    operators[entity_type] = OperatorConfig(
                        "replace", {"new_value": "[DATE]"}
                    )
                elif entity_type == "CREDIT_CARD":
                    operators[entity_type] = OperatorConfig(
                        "replace", {"new_value": "[CARD]"}
                    )
                else:
                    # Default operator for unknown entity types
                    operators[entity_type] = OperatorConfig(
                        "replace", {"new_value": "[REDACTED]"}
                    )

            return operators

        except ImportError:
            logger.warning("Presidio anonymizer not available")
            return {}

    def _get_default_anonymization_config(self) -> dict[str, Any]:
        """Get default configuration for anonymization methods."""
        return {
            # Global settings
            "prefer_presidio_for_text": True,
            "consistent_hashing": True,
            # Method-specific defaults
            "age_bins": [0, 18, 30, 45, 60, 100],
            "age_labels": ["Under 18", "18-29", "30-44", "45-59", "60+"],
            "income_bins": [0, 25000, 50000, 75000, 100000, float("inf")],
            "income_labels": ["Low", "Lower-Middle", "Middle", "Upper-Middle", "High"],
            "geo_level": "region",
            "date_precision": "month",
            "top_percentile": 95,
            "bottom_percentile": 5,
            "noise_type": "gaussian",
            "noise_level": 0.1,
        }

    def anonymize_text_content(
        self, text: str, entities_to_anonymize: list[str] | None = None
    ) -> str:
        """Anonymize text content using Presidio.

        Args:
            text: Text to anonymize
            entities_to_anonymize: Specific entity types to target

        Returns:
            Anonymized text

        """
        if self.presidio_analyzer.is_available():
            # Analyze first
            analysis_results = self.presidio_analyzer.analyze_text(text)

            # Filter to specific entities if requested
            if entities_to_anonymize:
                analysis_results = [
                    result
                    for result in analysis_results
                    if result["entity_type"] in entities_to_anonymize
                ]

            # Anonymize
            return self.presidio_analyzer.anonymize_text(text, analysis_results)
        else:
            # Fall back to basic text masking
            return self.current_techniques.text_masking(text)

    def get_available_methods(self) -> dict[str, dict[str, Any]]:
        """Get information about available anonymization methods."""
        methods = {
            "remove": {
                "description": "Complete removal of the column",
                "suitable_for": ["any"],
                "preserves_format": False,
            },
            "hash_pseudonymization": {
                "description": "Replace with consistent hash-based identifiers",
                "suitable_for": ["identifiers", "names"],
                "preserves_format": False,
            },
            "age_categorization": {
                "description": "Convert ages to categorical ranges",
                "suitable_for": ["numeric", "age"],
                "preserves_format": False,
            },
            "income_categorization": {
                "description": "Convert income to categorical ranges",
                "suitable_for": ["numeric", "income"],
                "preserves_format": False,
            },
            "geographic_generalization": {
                "description": "Generalize locations to broader regions",
                "suitable_for": ["location", "geographic"],
                "preserves_format": False,
            },
            "date_generalization": {
                "description": "Reduce date precision (year, month, quarter)",
                "suitable_for": ["date", "temporal"],
                "preserves_format": True,
            },
            "text_masking": {
                "description": "Mask PII patterns in text with placeholders",
                "suitable_for": ["text", "mixed"],
                "preserves_format": True,
            },
            "add_noise": {
                "description": "Add statistical noise to numeric values",
                "suitable_for": ["numeric"],
                "preserves_format": True,
            },
            "top_bottom_coding": {
                "description": "Cap extreme values in distributions",
                "suitable_for": ["numeric"],
                "preserves_format": True,
            },
        }

        # Add Presidio methods if available
        if self.presidio_analyzer.is_available():
            methods["presidio_replace"] = {
                "description": "Advanced text anonymization using Presidio ML models",
                "suitable_for": ["text", "mixed"],
                "preserves_format": True,
                "entity_types": self.presidio_analyzer.get_supported_entities(),
            }

        return methods


# Convenience functions


def anonymize_dataset_hybrid(
    dataset: pd.DataFrame,
    pii_columns: list[str] | dict[str, PIIDetectionResult],
    config: dict[str, Any] | None = None,
    language: str = "en",
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Perform hybrid dataset anonymization.

    Args:
        dataset: Original dataset
        pii_columns: PII columns to anonymize
        config: Anonymization configuration
        language: Language for text processing

    Returns:
        Tuple of (anonymized_dataset, anonymization_report)

    """
    anonymizer = HybridAnonymizer(language=language)
    return anonymizer.anonymize_dataset(dataset, pii_columns, config)
