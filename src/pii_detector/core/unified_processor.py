"""Unified PII detection processor combining structural analysis with Presidio text analysis.

This module provides a hybrid approach that combines:
1. Existing structural detection methods (column names, formats, sparsity, locations)
2. Advanced Presidio-powered text content analysis
3. Confidence-weighted scoring and decision making
"""

import logging
from typing import Any

import pandas as pd

from pii_detector.core import processor
from pii_detector.core.presidio_engine import get_presidio_analyzer
from pii_detector.data import constants

logger = logging.getLogger(__name__)


class PIIDetectionResult:
    """Represents a PII detection result with confidence scoring."""

    def __init__(
        self,
        column_name: str,
        detection_method: str,
        confidence: float,
        entity_types: list[str] | None = None,
        details: dict[str, Any] | None = None,
    ):
        """Initialize PII detection result.

        Args:
            column_name: Name of the column
            detection_method: Method used for detection
            confidence: Confidence score (0.0 to 1.0)
            entity_types: List of detected entity types
            details: Additional detection details

        """
        self.column_name = column_name
        self.detection_method = detection_method
        self.confidence = confidence
        self.entity_types = entity_types or []
        self.details = details or {}

    def __repr__(self) -> str:
        return f"PIIDetectionResult(column='{self.column_name}', method='{self.detection_method}', confidence={self.confidence:.2f})"


class UnifiedPIIProcessor:
    """Unified processor that combines structural and text-based PII detection."""

    def __init__(self, language: str = "en"):
        """Initialize the unified processor.

        Args:
            language: Language code for text analysis

        """
        self.language = language
        self.presidio_analyzer = get_presidio_analyzer(language)

    def detect_pii_comprehensive(
        self,
        dataset: pd.DataFrame,
        label_dict: dict[str, str] | None = None,
        detection_config: dict[str, Any] | None = None,
    ) -> dict[str, PIIDetectionResult]:
        """Perform comprehensive PII detection using all available methods.

        Args:
            dataset: The pandas DataFrame to analyze
            label_dict: Dictionary mapping column names to their labels
            detection_config: Configuration options for detection

        Returns:
            Dictionary mapping column names to detection results

        """
        if detection_config is None:
            detection_config = self._get_default_config()

        logger.info(
            f"Starting comprehensive PII detection on {len(dataset.columns)} columns"
        )

        results = {}

        # Run all detection methods
        structural_results = self._detect_structural_pii(
            dataset, label_dict, detection_config
        )
        text_content_results = self._detect_text_content_pii(dataset, detection_config)

        # Combine and score results
        all_detected_columns = set(structural_results.keys()) | set(
            text_content_results.keys()
        )

        for column_name in all_detected_columns:
            structural_result = structural_results.get(column_name)
            text_result = text_content_results.get(column_name)

            # Combine results with confidence weighting
            combined_result = self._combine_detection_results(
                column_name, structural_result, text_result, detection_config
            )

            if combined_result:
                results[column_name] = combined_result

        logger.info(
            f"PII detection completed. Found {len(results)} potentially sensitive columns"
        )
        return results

    def _detect_structural_pii(
        self,
        dataset: pd.DataFrame,
        label_dict: dict[str, str] | None,
        config: dict[str, Any],
    ) -> dict[str, PIIDetectionResult]:
        """Detect PII using structural analysis methods."""
        results = {}

        # Column name/label matching
        if config.get("use_column_name_detection", True):
            column_name_piis = processor.find_piis_based_on_column_name(
                dataset,
                label_dict or {},
                self.language,
                config.get("country", "US"),
                config.get("matching_type", constants.STRICT),
            )

            for column in column_name_piis:
                results[column] = PIIDetectionResult(
                    column_name=column,
                    detection_method="column_name_matching",
                    confidence=config.get("column_name_confidence", 0.8),
                    details={
                        "matching_type": config.get("matching_type", constants.STRICT)
                    },
                )

        # Format pattern detection
        if config.get("use_format_detection", True):
            format_piis = processor.find_piis_based_on_column_format(dataset)

            for column in format_piis:
                if column not in results:
                    results[column] = PIIDetectionResult(
                        column_name=column,
                        detection_method="format_patterns",
                        confidence=config.get("format_pattern_confidence", 0.9),
                    )

        # Sparsity analysis
        if config.get("use_sparsity_detection", True):
            sparsity_piis = processor.find_piis_based_on_sparse_entries(
                dataset, config.get("sparse_threshold", 0.8)
            )

            for column in sparsity_piis:
                if column not in results:
                    results[column] = PIIDetectionResult(
                        column_name=column,
                        detection_method="sparsity_analysis",
                        confidence=config.get("sparsity_confidence", 0.6),
                        details={
                            "sparse_threshold": config.get("sparse_threshold", 0.8)
                        },
                    )

        # Location population analysis
        if config.get("use_location_detection", True):
            location_piis = processor.find_piis_based_on_locations_population(
                dataset,
                config.get("population_threshold", 20000),
                config.get("country", "US"),
            )

            for column in location_piis:
                if column not in results:
                    results[column] = PIIDetectionResult(
                        column_name=column,
                        detection_method="location_population",
                        confidence=config.get("location_confidence", 0.7),
                        details={
                            "population_threshold": config.get(
                                "population_threshold", 20000
                            )
                        },
                    )

        return results

    def _detect_text_content_pii(
        self, dataset: pd.DataFrame, config: dict[str, Any]
    ) -> dict[str, PIIDetectionResult]:
        """Detect PII using Presidio text content analysis."""
        results = {}

        if not config.get("use_presidio_detection", True):
            return results

        if not self.presidio_analyzer.is_available():
            logger.warning("Presidio not available, skipping text content analysis")
            return results

        confidence_threshold = config.get("presidio_confidence_threshold", 0.7)
        sample_size = config.get("presidio_sample_size", 100)

        for column_name in dataset.columns:
            # Only analyze text-like columns
            if dataset[column_name].dtype == "object":
                try:
                    analysis_result = self.presidio_analyzer.analyze_column_text(
                        dataset[column_name],
                        confidence_threshold=confidence_threshold,
                        sample_size=sample_size,
                    )

                    if (
                        analysis_result.get("presidio_available", False)
                        and analysis_result.get("total_detections", 0) > 0
                    ):
                        # Calculate detection confidence based on results
                        avg_confidence = analysis_result.get("average_confidence", 0)
                        detection_rate = analysis_result.get(
                            "total_detections", 0
                        ) / analysis_result.get("sample_analyzed", 1)

                        # Adjust confidence based on detection rate
                        adjusted_confidence = min(
                            avg_confidence * (1 + detection_rate), 1.0
                        )

                        if adjusted_confidence >= confidence_threshold:
                            entity_types = list(
                                analysis_result.get("entities_found", {}).keys()
                            )

                            results[column_name] = PIIDetectionResult(
                                column_name=column_name,
                                detection_method="presidio_text_analysis",
                                confidence=adjusted_confidence,
                                entity_types=entity_types,
                                details={
                                    "total_detections": analysis_result.get(
                                        "total_detections", 0
                                    ),
                                    "average_confidence": avg_confidence,
                                    "detection_rate": detection_rate,
                                    "entities_found": analysis_result.get(
                                        "entities_found", {}
                                    ),
                                },
                            )

                except Exception as e:
                    logger.error(
                        f"Error analyzing column {column_name} with Presidio: {e}"
                    )

        return results

    def _combine_detection_results(
        self,
        column_name: str,
        structural_result: PIIDetectionResult | None,
        text_result: PIIDetectionResult | None,
        config: dict[str, Any],
    ) -> PIIDetectionResult | None:
        """Combine structural and text detection results with confidence weighting."""
        if structural_result is None and text_result is None:
            return None

        if structural_result is None:
            return text_result

        if text_result is None:
            return structural_result

        # Both results exist - combine them
        structural_weight = config.get("structural_weight", 0.6)
        text_weight = config.get("text_weight", 0.4)

        combined_confidence = (
            structural_result.confidence * structural_weight
            + text_result.confidence * text_weight
        )

        # Combine entity types
        combined_entity_types = list(
            set(structural_result.entity_types + text_result.entity_types)
        )

        # Combine details
        combined_details = {
            "structural_detection": {
                "method": structural_result.detection_method,
                "confidence": structural_result.confidence,
                "details": structural_result.details,
            },
            "text_detection": {
                "method": text_result.detection_method,
                "confidence": text_result.confidence,
                "entity_types": text_result.entity_types,
                "details": text_result.details,
            },
            "combined_weights": {"structural": structural_weight, "text": text_weight},
        }

        return PIIDetectionResult(
            column_name=column_name,
            detection_method="hybrid_detection",
            confidence=combined_confidence,
            entity_types=combined_entity_types,
            details=combined_details,
        )

    def _get_default_config(self) -> dict[str, Any]:
        """Get default configuration for PII detection."""
        return {
            # Structural detection options
            "use_column_name_detection": True,
            "use_format_detection": True,
            "use_sparsity_detection": True,
            "use_location_detection": True,
            # Presidio options
            "use_presidio_detection": True,
            "presidio_confidence_threshold": 0.7,
            "presidio_sample_size": 100,
            # Confidence scores for structural methods
            "column_name_confidence": 0.8,
            "format_pattern_confidence": 0.9,
            "sparsity_confidence": 0.6,
            "location_confidence": 0.7,
            # Combination weights
            "structural_weight": 0.6,
            "text_weight": 0.4,
            # Other parameters
            "matching_type": constants.STRICT,
            "sparse_threshold": 0.8,
            "population_threshold": 20000,
            "country": "US",
        }

    def get_high_confidence_detections(
        self, results: dict[str, PIIDetectionResult], threshold: float = 0.8
    ) -> dict[str, PIIDetectionResult]:
        """Filter results to only high-confidence detections."""
        return {
            col: result
            for col, result in results.items()
            if result.confidence >= threshold
        }

    def get_detection_summary(
        self, results: dict[str, PIIDetectionResult]
    ) -> dict[str, Any]:
        """Generate a summary of detection results."""
        if not results:
            return {"total_columns": 0, "total_detections": 0}

        methods = {}
        entity_types = {}
        confidence_scores = []

        for result in results.values():
            # Count methods
            method = result.detection_method
            methods[method] = methods.get(method, 0) + 1

            # Count entity types
            for entity_type in result.entity_types:
                entity_types[entity_type] = entity_types.get(entity_type, 0) + 1

            confidence_scores.append(result.confidence)

        return {
            "total_detections": len(results),
            "methods_used": methods,
            "entity_types_found": entity_types,
            "average_confidence": sum(confidence_scores) / len(confidence_scores),
            "confidence_distribution": {
                "high": len([c for c in confidence_scores if c >= 0.8]),
                "medium": len([c for c in confidence_scores if 0.6 <= c < 0.8]),
                "low": len([c for c in confidence_scores if c < 0.6]),
            },
        }


# Convenience functions for backward compatibility


def detect_pii_unified(
    dataset: pd.DataFrame,
    label_dict: dict[str, str] | None = None,
    language: str = "en",
    config: dict[str, Any] | None = None,
) -> dict[str, PIIDetectionResult]:
    """Perform unified PII detection.

    Args:
        dataset: The pandas DataFrame to analyze
        label_dict: Dictionary mapping column names to their labels
        language: Language code for text analysis
        config: Detection configuration options

    Returns:
        Dictionary mapping column names to detection results

    """
    processor_instance = UnifiedPIIProcessor(language=language)
    return processor_instance.detect_pii_comprehensive(dataset, label_dict, config)


def get_pii_column_list(results: dict[str, PIIDetectionResult]) -> list[str]:
    """Extract list of column names from detection results.

    Args:
        results: Detection results from unified processor

    Returns:
        List of column names identified as containing PII

    """
    return list(results.keys())
