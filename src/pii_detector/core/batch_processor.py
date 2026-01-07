"""Efficient batch processing for PII detection and anonymization using Presidio.

This module implements efficient batch processing techniques for structured data,
incorporating Presidio's BatchAnalyzerEngine and presidio-structured capabilities.
"""

import logging
from collections import defaultdict
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from typing import Any

import pandas as pd

from pii_detector.core.hybrid_anonymizer import HybridAnonymizer
from pii_detector.core.presidio_engine import get_presidio_analyzer
from pii_detector.core.unified_processor import PIIDetectionResult, UnifiedPIIProcessor

logger = logging.getLogger(__name__)

# Optional imports for advanced batch processing
try:
    from presidio_structured import StructuredEngine
    from presidio_structured.config import StructuredAnalysisConfig

    PRESIDIO_STRUCTURED_AVAILABLE = True
    logger.info("presidio-structured available for advanced batch processing")
except ImportError:
    PRESIDIO_STRUCTURED_AVAILABLE = False
    logger.info("presidio-structured not available, using standard batch processing")

try:
    from presidio_analyzer import BatchAnalyzerEngine

    BATCH_ANALYZER_AVAILABLE = True
except ImportError:
    BATCH_ANALYZER_AVAILABLE = False


class BatchPIIProcessor:
    """Enhanced batch processor for efficient PII detection and anonymization."""

    def __init__(
        self,
        language: str = "en",
        chunk_size: int = 1000,
        max_workers: int = 4,
        use_structured_engine: bool = False,  # Default to False for better compatibility
    ):
        """Initialize batch processor.

        Args:
            language: Language code for text analysis
            chunk_size: Number of rows to process per chunk
            max_workers: Maximum number of parallel workers
            use_structured_engine: Whether to use presidio-structured if available

        """
        self.language = language
        self.chunk_size = chunk_size
        self.max_workers = max_workers
        self.use_structured_engine = (
            use_structured_engine and PRESIDIO_STRUCTURED_AVAILABLE
        )

        # Initialize processors
        self.unified_processor = UnifiedPIIProcessor(language=language)
        self.hybrid_anonymizer = HybridAnonymizer(language=language)
        self.presidio_analyzer = get_presidio_analyzer(language=language)

        # Initialize structured engine if available
        if self.use_structured_engine:
            self._init_structured_engine()

        # Initialize batch analyzer if available
        self.batch_analyzer = None
        if BATCH_ANALYZER_AVAILABLE and self.presidio_analyzer.is_available():
            try:
                self.batch_analyzer = BatchAnalyzerEngine(
                    analyzer_engine=self.presidio_analyzer.analyzer
                )
                logger.info("BatchAnalyzerEngine initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to initialize BatchAnalyzerEngine: {e}")

    def _safe_callback(self, callback: Callable | None, progress: float, message: str):
        """Safely call progress callback, catching any exceptions.

        Args:
            callback: Progress callback function
            progress: Progress percentage (0-100)
            message: Progress message

        """
        if callback:
            try:
                callback(progress, message)
            except Exception as e:
                logger.warning(f"Progress callback raised exception: {e}")

    def _init_structured_engine(self):
        """Initialize the structured engine for advanced processing."""
        try:
            if not PRESIDIO_STRUCTURED_AVAILABLE:
                logger.info(
                    "presidio-structured not available, skipping structured engine initialization"
                )
                self.use_structured_engine = False
                return

            # Try to configure structured analysis with basic config
            try:
                structured_config = StructuredAnalysisConfig(
                    analyzer_config={
                        "supported_languages": [self.language],
                        "default_score_threshold": 0.7,
                    }
                )
                self.structured_engine = StructuredEngine(config=structured_config)
            except (TypeError, AttributeError) as config_error:
                # Try with simpler configuration if the above fails
                logger.info(
                    f"Advanced config failed ({config_error}), trying basic config"
                )
                self.structured_engine = StructuredEngine()

            logger.info("StructuredEngine initialized successfully")
        except Exception as e:
            logger.warning(f"Failed to initialize StructuredEngine: {e}")
            self.use_structured_engine = False

    def detect_pii_batch(
        self,
        dataset: pd.DataFrame,
        label_dict: dict[str, str] | None = None,
        detection_config: dict[str, Any] | None = None,
        progress_callback: Callable | None = None,
    ) -> dict[str, PIIDetectionResult]:
        """Perform batch PII detection with optimized processing.

        Args:
            dataset: DataFrame to analyze
            label_dict: Column labels mapping
            detection_config: Detection configuration
            progress_callback: Optional callback for progress reporting

        Returns:
            Dictionary of PII detection results

        """
        logger.info(
            f"Starting batch PII detection on dataset with shape {dataset.shape}"
        )

        if detection_config is None:
            detection_config = self._get_optimized_detection_config()

        # Choose processing strategy based on dataset size and available tools
        if self.use_structured_engine and len(dataset) > self.chunk_size:
            return self._detect_with_structured_engine(
                dataset, label_dict, detection_config, progress_callback
            )
        elif len(dataset) > self.chunk_size * 2:
            return self._detect_with_chunking(
                dataset, label_dict, detection_config, progress_callback
            )
        else:
            return self._detect_standard(
                dataset, label_dict, detection_config, progress_callback
            )

    def _detect_with_structured_engine(
        self,
        dataset: pd.DataFrame,
        label_dict: dict[str, str] | None,
        config: dict[str, Any],
        progress_callback: Callable | None = None,
    ) -> dict[str, PIIDetectionResult]:
        """Use presidio-structured for efficient batch processing."""
        logger.info("Using presidio-structured for batch detection")
        results = {}

        try:
            # Analyze with structured engine
            structured_results = self.structured_engine.analyze(dataset)

            # Convert structured results to our format
            for column_name, analysis_result in structured_results.items():
                if (
                    hasattr(analysis_result, "entity_types")
                    and analysis_result.entity_types
                ):
                    results[column_name] = PIIDetectionResult(
                        column_name=column_name,
                        detection_method="presidio_structured",
                        confidence=getattr(analysis_result, "score", 0.8),
                        entity_types=list(analysis_result.entity_types),
                        details={
                            "structured_analysis": True,
                            "detection_count": getattr(
                                analysis_result, "detection_count", 0
                            ),
                        },
                    )

            # Combine with structural analysis for comprehensive results
            structural_results = self.unified_processor._detect_structural_pii(
                dataset, label_dict or {}, config
            )

            # Merge results with preference for structured analysis
            for col, struct_result in structural_results.items():
                if col not in results:
                    results[col] = struct_result
                else:
                    # Combine confidence scores
                    existing = results[col]
                    combined_confidence = (
                        existing.confidence * 0.7 + struct_result.confidence * 0.3
                    )
                    results[col] = PIIDetectionResult(
                        column_name=col,
                        detection_method="hybrid_structured",
                        confidence=combined_confidence,
                        entity_types=list(
                            set(existing.entity_types + struct_result.entity_types)
                        ),
                        details={
                            "presidio_structured": existing.details,
                            "structural_analysis": struct_result.details,
                        },
                    )

        except Exception as e:
            logger.error(f"Error in structured engine processing: {e}")
            return self._detect_standard(dataset, label_dict, config, progress_callback)

        self._safe_callback(progress_callback, 100, "Structured analysis complete")

        return results

    def _detect_with_chunking(
        self,
        dataset: pd.DataFrame,
        label_dict: dict[str, str] | None,
        config: dict[str, Any],
        progress_callback: Callable | None = None,
    ) -> dict[str, PIIDetectionResult]:
        """Process large datasets in chunks with parallel processing."""
        logger.info(f"Processing dataset in chunks of {self.chunk_size} rows")

        # First, do structural analysis on the full dataset (doesn't depend on row content)
        structural_results = self.unified_processor._detect_structural_pii(
            dataset, label_dict or {}, config
        )

        # For text content analysis, process in chunks
        text_results = defaultdict(list)
        total_chunks = len(dataset) // self.chunk_size + (
            1 if len(dataset) % self.chunk_size else 0
        )

        # Process text columns in parallel chunks
        text_columns = [
            col for col in dataset.columns if dataset[col].dtype == "object"
        ]

        if text_columns and self.presidio_analyzer.is_available():
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                futures = []

                for i, start_idx in enumerate(range(0, len(dataset), self.chunk_size)):
                    end_idx = min(start_idx + self.chunk_size, len(dataset))
                    chunk = dataset.iloc[start_idx:end_idx]

                    future = executor.submit(
                        self._analyze_chunk_text_content, chunk, text_columns, config
                    )
                    futures.append((future, i))

                # Collect results
                for future, chunk_idx in futures:
                    try:
                        chunk_results = future.result()
                        for col, result in chunk_results.items():
                            text_results[col].append(result)

                        progress = ((chunk_idx + 1) / total_chunks) * 100
                        self._safe_callback(
                            progress_callback,
                            progress,
                            f"Processed chunk {chunk_idx + 1}/{total_chunks}",
                        )

                    except Exception as e:
                        logger.error(f"Error processing chunk {chunk_idx}: {e}")

        # Aggregate text results
        aggregated_text_results = self._aggregate_chunk_results(text_results, config)

        # Combine structural and text results
        final_results = {}
        all_columns = set(structural_results.keys()) | set(
            aggregated_text_results.keys()
        )

        for col in all_columns:
            structural = structural_results.get(col)
            text = aggregated_text_results.get(col)

            combined = self.unified_processor._combine_detection_results(
                col, structural, text, config
            )
            if combined:
                final_results[col] = combined

        return final_results

    def _analyze_chunk_text_content(
        self, chunk: pd.DataFrame, text_columns: list[str], config: dict[str, Any]
    ) -> dict[str, Any]:
        """Analyze text content in a data chunk."""
        results = {}

        for col in text_columns:
            if col not in chunk.columns:
                continue

            try:
                analysis = self.presidio_analyzer.analyze_column_text(
                    chunk[col],
                    confidence_threshold=config.get(
                        "presidio_confidence_threshold", 0.7
                    ),
                    sample_size=config.get("presidio_sample_size", 100),
                )

                if analysis.get("total_detections", 0) > 0:
                    results[col] = analysis

            except Exception as e:
                logger.error(f"Error analyzing chunk for column {col}: {e}")

        return results

    def _aggregate_chunk_results(
        self, chunk_results: dict[str, list[dict[str, Any]]], config: dict[str, Any]
    ) -> dict[str, PIIDetectionResult]:
        """Aggregate results from multiple chunks."""
        aggregated = {}

        for col, results_list in chunk_results.items():
            if not results_list:
                continue

            # Combine detection statistics
            total_detections = sum(r.get("total_detections", 0) for r in results_list)
            total_samples = sum(r.get("sample_analyzed", 0) for r in results_list)
            all_scores = []
            all_entities = defaultdict(int)

            for result in results_list:
                all_scores.extend(result.get("confidence_scores", []))
                for entity_type, entities in result.get("entities_found", {}).items():
                    all_entities[entity_type] += len(entities)

            if total_detections > 0 and all_scores:
                avg_confidence = sum(all_scores) / len(all_scores)
                detection_rate = total_detections / max(total_samples, 1)
                adjusted_confidence = min(avg_confidence * (1 + detection_rate), 1.0)

                confidence_threshold = config.get("presidio_confidence_threshold", 0.7)
                if adjusted_confidence >= confidence_threshold:
                    aggregated[col] = PIIDetectionResult(
                        column_name=col,
                        detection_method="presidio_batch_text",
                        confidence=adjusted_confidence,
                        entity_types=list(all_entities.keys()),
                        details={
                            "total_detections": total_detections,
                            "total_samples": total_samples,
                            "detection_rate": detection_rate,
                            "entities_found": dict(all_entities),
                            "batch_processed": True,
                        },
                    )

        return aggregated

    def _detect_standard(
        self,
        dataset: pd.DataFrame,
        label_dict: dict[str, str] | None,
        config: dict[str, Any],
        progress_callback: Callable | None = None,
    ) -> dict[str, PIIDetectionResult]:
        """Run standard detection for smaller datasets."""
        results = self.unified_processor.detect_pii_comprehensive(
            dataset, label_dict, config
        )

        self._safe_callback(progress_callback, 100, "Standard detection complete")

        return results

    def anonymize_batch(
        self,
        dataset: pd.DataFrame,
        pii_results: dict[str, PIIDetectionResult],
        anonymization_config: dict[str, Any] | None = None,
        progress_callback: Callable | None = None,
    ) -> tuple[pd.DataFrame, dict[str, Any]]:
        """Perform batch anonymization with optimized processing."""
        logger.info(f"Starting batch anonymization of {len(pii_results)} PII columns")

        if len(dataset) > self.chunk_size * 2:
            return self._anonymize_with_chunking(
                dataset, pii_results, anonymization_config, progress_callback
            )
        else:
            return self.hybrid_anonymizer.anonymize_dataset(
                dataset, pii_results, anonymization_config
            )

    def _anonymize_with_chunking(
        self,
        dataset: pd.DataFrame,
        pii_results: dict[str, PIIDetectionResult],
        config: dict[str, Any] | None,
        progress_callback: Callable | None = None,
    ) -> tuple[pd.DataFrame, dict[str, Any]]:
        """Anonymize large datasets in chunks."""
        logger.info(f"Anonymizing dataset in chunks of {self.chunk_size} rows")

        anonymized_chunks = []
        total_chunks = len(dataset) // self.chunk_size + (
            1 if len(dataset) % self.chunk_size else 0
        )

        # Process chunks in parallel for columns that support it
        text_pii_columns = {
            col: result
            for col, result in pii_results.items()
            if result.detection_method
            in ["presidio_text_analysis", "presidio_batch_text", "hybrid_detection"]
            and dataset[col].dtype == "object"
        }

        # Non-text columns can be processed normally
        non_text_pii = {
            col: result
            for col, result in pii_results.items()
            if col not in text_pii_columns
        }

        for i, start_idx in enumerate(range(0, len(dataset), self.chunk_size)):
            end_idx = min(start_idx + self.chunk_size, len(dataset))
            chunk = dataset.iloc[start_idx:end_idx].copy()

            # Anonymize text columns with Presidio
            for col, detection_result in text_pii_columns.items():
                if col in chunk.columns:
                    anonymized_col = self._anonymize_column_presidio_batch(
                        chunk[col], detection_result, config
                    )
                    chunk[col] = anonymized_col

            # Anonymize non-text columns with standard methods
            if non_text_pii:
                chunk, _ = self.hybrid_anonymizer.anonymize_dataset(
                    chunk, non_text_pii, config
                )

            anonymized_chunks.append(chunk)

            progress = ((i + 1) / total_chunks) * 100
            self._safe_callback(
                progress_callback, progress, f"Anonymized chunk {i + 1}/{total_chunks}"
            )

        # Combine chunks
        final_dataset = pd.concat(anonymized_chunks, ignore_index=True)

        # Generate report
        report = {
            "original_shape": dataset.shape,
            "final_shape": final_dataset.shape,
            "chunks_processed": total_chunks,
            "batch_anonymization": True,
            "pii_columns": list(pii_results.keys()),
        }

        return final_dataset, report

    def _anonymize_column_presidio_batch(
        self,
        column_data: pd.Series,
        detection_result: PIIDetectionResult,
        config: dict[str, Any] | None,
    ) -> pd.Series:
        """Anonymize a column using Presidio with batch optimization."""
        if not self.presidio_analyzer.is_available():
            return column_data

        def anonymize_text_value(text_value):
            if isinstance(text_value, str) and len(text_value.strip()) > 0:
                return self.presidio_analyzer.anonymize_text(text_value)
            return text_value

        return column_data.apply(anonymize_text_value)

    def _get_optimized_detection_config(self) -> dict[str, Any]:
        """Get optimized configuration for batch processing."""
        config = self.unified_processor._get_default_config()

        # Optimize for batch processing
        config.update(
            {
                "presidio_sample_size": min(
                    200, self.chunk_size // 5
                ),  # Sample more for larger chunks
                "presidio_confidence_threshold": 0.6,  # Slightly lower threshold for batch
                "use_presidio_detection": self.presidio_analyzer.is_available(),
                "batch_processing": True,
            }
        )

        return config

    def get_processing_strategy(self, dataset: pd.DataFrame) -> str:
        """Determine the best processing strategy for a dataset."""
        row_count = len(dataset)

        if self.use_structured_engine and row_count > 1000:
            return "structured_engine"
        elif row_count > self.chunk_size * 2:
            return "chunked_processing"
        else:
            return "standard_processing"

    def estimate_processing_time(self, dataset: pd.DataFrame) -> dict[str, Any]:
        """Estimate processing time for different strategies."""
        row_count = len(dataset)
        col_count = len(dataset.columns)
        text_cols = sum(1 for col in dataset.columns if dataset[col].dtype == "object")

        # Rough estimates based on typical performance
        estimates = {
            "standard_processing": {
                "time_seconds": (row_count * text_cols * 0.001),
                "memory_mb": (row_count * col_count * 0.0001),
                "recommended": row_count < 10000,
            },
            "chunked_processing": {
                "time_seconds": (row_count * text_cols * 0.0008),
                "memory_mb": (self.chunk_size * col_count * 0.0001),
                "recommended": 10000 <= row_count < 100000,
            },
        }

        if self.use_structured_engine:
            estimates["structured_engine"] = {
                "time_seconds": (row_count * text_cols * 0.0005),
                "memory_mb": (row_count * col_count * 0.00008),
                "recommended": row_count >= 1000,
            }

        return estimates


# Convenience functions


def process_dataset_batch(
    dataset: pd.DataFrame,
    label_dict: dict[str, str] | None = None,
    language: str = "en",
    detection_config: dict[str, Any] | None = None,
    anonymization_config: dict[str, Any] | None = None,
    chunk_size: int = 1000,
    max_workers: int = 4,
    progress_callback: Callable | None = None,
) -> tuple[dict[str, PIIDetectionResult], pd.DataFrame, dict[str, Any]]:
    """Complete batch processing workflow for PII detection and anonymization.

    Args:
        dataset: Input dataset
        label_dict: Column labels mapping
        language: Language for text processing
        detection_config: Detection configuration
        anonymization_config: Anonymization configuration
        chunk_size: Chunk size for processing
        max_workers: Maximum parallel workers
        progress_callback: Progress callback function

    Returns:
        Tuple of (detection_results, anonymized_dataset, report)

    """
    processor = BatchPIIProcessor(
        language=language, chunk_size=chunk_size, max_workers=max_workers
    )

    # Detection phase
    detection_results = processor.detect_pii_batch(
        dataset, label_dict, detection_config, progress_callback
    )

    # Anonymization phase
    anonymized_dataset, anonymization_report = processor.anonymize_batch(
        dataset, detection_results, anonymization_config, progress_callback
    )

    return detection_results, anonymized_dataset, anonymization_report
