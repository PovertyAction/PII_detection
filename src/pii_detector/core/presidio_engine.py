"""Presidio integration engine for advanced PII detection and anonymization.

This module provides a wrapper around Microsoft Presidio's analyzer and anonymizer
engines, with graceful degradation if Presidio dependencies are not available.
"""

import logging
from typing import Any

import pandas as pd

logger = logging.getLogger(__name__)

# Reduce logging noise from Presidio
presidio_loggers = [
    "presidio-analyzer",
    "presidio_analyzer",
    "presidio_anonymizer",
    "presidio-anonymizer",
    "spacy",
]
for logger_name in presidio_loggers:
    logging.getLogger(logger_name).setLevel(logging.WARNING)

# Global flags for availability
PRESIDIO_AVAILABLE = False
PRESIDIO_ANALYZER = None
PRESIDIO_ANONYMIZER = None

try:
    from presidio_analyzer import AnalyzerEngine, RecognizerResult  # noqa: F401
    from presidio_anonymizer import AnonymizerEngine
    from presidio_anonymizer.entities import OperatorConfig

    PRESIDIO_AVAILABLE = True
    logger.info("Presidio successfully imported")
except ImportError as e:
    logger.warning(f"Presidio not available: {e}. Falling back to basic text analysis.")

# Import model manager for dynamic spaCy model handling
try:
    from pii_detector.core.model_manager import ensure_spacy_model

    MODEL_MANAGER_AVAILABLE = True
except ImportError:
    MODEL_MANAGER_AVAILABLE = False


class PresidioTextAnalyzer:
    """Presidio-powered text analysis for advanced PII detection."""

    def __init__(self, language: str = "en", preferred_model_size: str = "sm"):
        """Initialize the Presidio analyzer.

        Args:
            language: Language code for analysis (default: 'en')
            preferred_model_size: Preferred spaCy model size ('sm', 'md', 'lg')

        """
        self.language = language
        self.preferred_model_size = preferred_model_size
        self.analyzer = None
        self.anonymizer = None
        self.available = PRESIDIO_AVAILABLE
        self.spacy_model = None

        if self.available:
            try:
                # Ensure spaCy model is available
                if MODEL_MANAGER_AVAILABLE:
                    self.spacy_model = ensure_spacy_model(
                        language, preferred_model_size
                    )
                    if self.spacy_model:
                        logger.info(f"Using spaCy model: {self.spacy_model}")
                    else:
                        logger.warning(
                            f"No spaCy model available for language {language}"
                        )

                # Initialize Presidio engines
                # If we have a specific model, configure the analyzer to use it
                if self.spacy_model:
                    from presidio_analyzer import AnalyzerEngine, RecognizerRegistry
                    from presidio_analyzer.nlp_engine import NlpEngineProvider

                    # Create NLP configuration with reduced warnings
                    nlp_configuration = {
                        "nlp_engine_name": "spacy",
                        "models": [
                            {"lang_code": language, "model_name": self.spacy_model}
                        ],
                        "ner_model_configuration": {
                            "labels_to_ignore": [
                                "CARDINAL",
                                "FAC",
                                "EVENT",
                                "LAW",
                                "LANGUAGE",
                                "WORK_OF_ART",
                                "ORDINAL",
                                "QUANTITY",
                                "DATE",
                            ],
                            "model_to_presidio_entity_mapping": {
                                "PERSON": "PERSON",
                                "GPE": "LOCATION",
                                "ORG": "ORGANIZATION",
                            },
                            "low_score_entity_names": [],
                        },
                    }
                    nlp_engine = NlpEngineProvider(
                        nlp_configuration=nlp_configuration
                    ).create_engine()

                    # Create registry and analyzer
                    registry = RecognizerRegistry()
                    registry.load_predefined_recognizers(nlp_engine=nlp_engine)
                    self.analyzer = AnalyzerEngine(
                        nlp_engine=nlp_engine, registry=registry
                    )
                else:
                    # Use default configuration with reduced warnings
                    self.analyzer = AnalyzerEngine()

                self.anonymizer = AnonymizerEngine()
                logger.info("Presidio engines initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Presidio engines: {e}")
                self.available = False

    def is_available(self) -> bool:
        """Check if Presidio is available and properly initialized."""
        return self.available and self.analyzer is not None

    def analyze_text(
        self,
        text: str,
        entities: list[str] | None = None,
        confidence_threshold: float = 0.7,
    ) -> list[dict[str, Any]]:
        """Analyze text for PII entities using Presidio.

        Args:
            text: Text to analyze
            entities: List of entity types to look for (None = all)
            confidence_threshold: Minimum confidence score

        Returns:
            List of detected PII entities with metadata

        """
        if not self.is_available():
            logger.warning("Presidio not available, returning empty results")
            return []

        if not text or not isinstance(text, str):
            return []

        try:
            # Use Presidio analyzer
            results = self.analyzer.analyze(
                text=text, entities=entities, language=self.language
            )

            # Filter by confidence and format results
            formatted_results = []
            for result in results:
                if result.score >= confidence_threshold:
                    formatted_results.append(
                        {
                            "entity_type": result.entity_type,
                            "start": result.start,
                            "end": result.end,
                            "score": result.score,
                            "text": text[result.start : result.end],
                        }
                    )

            return formatted_results

        except Exception as e:
            logger.error(f"Error analyzing text with Presidio: {e}")
            return []

    def _analyze_text_batch(
        self, text_batch: pd.Series, confidence_threshold: float
    ) -> tuple[list[dict[str, Any]], list[float]]:
        """Analyze a batch of text values efficiently.

        Args:
            text_batch: Series of text values to analyze
            confidence_threshold: Minimum confidence threshold

        Returns:
            Tuple of (all_entities, all_scores)

        """
        all_entities = []
        all_scores = []

        try:
            # Try to use batch analyzer if available
            if hasattr(self, "_batch_analyzer") and self._batch_analyzer:
                # Convert to list and filter valid texts
                texts = [
                    str(text)
                    for text in text_batch
                    if isinstance(text, str) and len(str(text).strip()) > 0
                ]

                if texts:
                    batch_results = self._batch_analyzer.analyze_iterator(
                        texts, language=self.language
                    )

                    for result_list in batch_results:
                        for result in result_list:
                            if result.score >= confidence_threshold:
                                all_entities.append(
                                    {
                                        "entity_type": result.entity_type,
                                        "start": result.start,
                                        "end": result.end,
                                        "score": result.score,
                                        "text": texts[0][
                                            result.start : result.end
                                        ],  # Approximate
                                    }
                                )
                                all_scores.append(result.score)
            else:
                # Fall back to individual processing
                for text_value in text_batch:
                    if isinstance(text_value, str) and len(text_value.strip()) > 0:
                        entities = self.analyze_text(
                            text_value, confidence_threshold=confidence_threshold
                        )
                        all_entities.extend(entities)
                        all_scores.extend([entity["score"] for entity in entities])

        except Exception as e:
            logger.warning(f"Batch processing failed, falling back to individual: {e}")
            # Fall back to individual processing
            for text_value in text_batch:
                if isinstance(text_value, str) and len(text_value.strip()) > 0:
                    entities = self.analyze_text(
                        text_value, confidence_threshold=confidence_threshold
                    )
                    all_entities.extend(entities)
                    all_scores.extend([entity["score"] for entity in entities])

        return all_entities, all_scores

    def analyze_column_text(
        self,
        column_data: pd.Series,
        confidence_threshold: float = 0.7,
        sample_size: int = 100,
        batch_size: int | None = None,
    ) -> dict[str, Any]:
        """Analyze text content in a pandas column with optional batch processing.

        Args:
            column_data: Pandas Series containing text data
            confidence_threshold: Minimum confidence for detection
            sample_size: Maximum number of samples to analyze
            batch_size: Optional batch size for processing large columns

        Returns:
            Dictionary with analysis results and statistics

        """
        if not self.is_available():
            return {
                "presidio_available": False,
                "entities_found": [],
                "total_detections": 0,
                "confidence_scores": [],
                "sample_analyzed": 0,
            }

        # Clean and sample the data
        clean_data = column_data.dropna()
        clean_data = clean_data[clean_data.astype(str).str.strip() != ""]

        if len(clean_data) == 0:
            return {
                "presidio_available": True,
                "entities_found": [],
                "total_detections": 0,
                "confidence_scores": [],
                "sample_analyzed": 0,
            }

        # Sample data for analysis
        sample_data = clean_data.head(min(sample_size, len(clean_data)))

        all_entities = []
        all_scores = []

        # Process in batches if batch_size is specified and we have many samples
        if batch_size and len(sample_data) > batch_size:
            for i in range(0, len(sample_data), batch_size):
                batch = sample_data.iloc[i : i + batch_size]
                batch_entities, batch_scores = self._analyze_text_batch(
                    batch, confidence_threshold
                )
                all_entities.extend(batch_entities)
                all_scores.extend(batch_scores)
        else:
            # Process individually
            for text_value in sample_data:
                if isinstance(text_value, str) and len(text_value.strip()) > 0:
                    entities = self.analyze_text(
                        text_value, confidence_threshold=confidence_threshold
                    )
                    all_entities.extend(entities)
                    all_scores.extend([entity["score"] for entity in entities])

        # Aggregate results
        entity_types = {}
        for entity in all_entities:
            entity_type = entity["entity_type"]
            if entity_type not in entity_types:
                entity_types[entity_type] = []
            entity_types[entity_type].append(entity)

        return {
            "presidio_available": True,
            "entities_found": entity_types,
            "total_detections": len(all_entities),
            "confidence_scores": all_scores,
            "sample_analyzed": len(sample_data),
            "average_confidence": sum(all_scores) / len(all_scores)
            if all_scores
            else 0,
        }

    def anonymize_text(
        self,
        text: str,
        analyzer_results: list[dict[str, Any]] | None = None,
        operators: dict[str, Any] | None = None,
    ) -> str:
        """Anonymize text using Presidio.

        Args:
            text: Text to anonymize
            analyzer_results: Pre-computed analysis results
            operators: Custom operators for anonymization

        Returns:
            Anonymized text

        """
        if not self.is_available():
            logger.warning("Presidio not available, returning original text")
            return text

        if not text or not isinstance(text, str):
            return text

        try:
            # If no analysis results provided, analyze first
            if analyzer_results is None:
                presidio_results = self.analyzer.analyze(
                    text=text, language=self.language
                )
            else:
                # Convert our format back to Presidio format
                presidio_results = []
                for result in analyzer_results:
                    presidio_results.append(
                        RecognizerResult(
                            entity_type=result["entity_type"],
                            start=result["start"],
                            end=result["end"],
                            score=result["score"],
                        )
                    )

            # Default operators
            if operators is None:
                operators = {
                    "PERSON": OperatorConfig("replace", {"new_value": "[PERSON]"}),
                    "PHONE_NUMBER": OperatorConfig("replace", {"new_value": "[PHONE]"}),
                    "EMAIL_ADDRESS": OperatorConfig(
                        "replace", {"new_value": "[EMAIL]"}
                    ),
                    "LOCATION": OperatorConfig("replace", {"new_value": "[LOCATION]"}),
                    "DATE_TIME": OperatorConfig("replace", {"new_value": "[DATE]"}),
                    "US_SSN": OperatorConfig("replace", {"new_value": "[SSN]"}),
                    "CREDIT_CARD": OperatorConfig("replace", {"new_value": "[CARD]"}),
                    "US_DRIVER_LICENSE": OperatorConfig(
                        "replace", {"new_value": "[LICENSE]"}
                    ),
                    "DEFAULT": OperatorConfig("replace", {"new_value": "[REDACTED]"}),
                }

            # Anonymize the text
            anonymized_result = self.anonymizer.anonymize(
                text=text, analyzer_results=presidio_results, operators=operators
            )

            return anonymized_result.text

        except Exception as e:
            logger.error(f"Error anonymizing text with Presidio: {e}")
            return text

    def get_supported_entities(self) -> list[str]:
        """Get list of supported entity types.

        Returns:
            List of entity type names

        """
        if not self.is_available():
            return []

        try:
            # Get supported recognizers from Presidio
            supported_entities = []
            for recognizer in self.analyzer.registry.recognizers:
                supported_entities.extend(recognizer.supported_entities)

            return list(set(supported_entities))

        except Exception as e:
            logger.error(f"Error getting supported entities: {e}")
            return []

    def get_recognizer_info(self) -> dict[str, list[str]]:
        """Get detailed information about available recognizers.

        Returns:
            Dictionary mapping recognizer names to supported entities

        """
        if not self.is_available():
            return {}

        try:
            recognizer_info = {}
            for recognizer in self.analyzer.registry.recognizers:
                recognizer_name = recognizer.__class__.__name__
                recognizer_info[recognizer_name] = recognizer.supported_entities

            return recognizer_info

        except Exception as e:
            logger.error(f"Error getting recognizer info: {e}")
            return {}


# Singleton instance for global use
_presidio_analyzer = None


def get_presidio_analyzer(
    language: str = "en", preferred_model_size: str = "sm"
) -> PresidioTextAnalyzer:
    """Get or create a Presidio analyzer instance.

    Args:
        language: Language code for the analyzer
        preferred_model_size: Preferred spaCy model size

    Returns:
        PresidioTextAnalyzer instance

    """
    global _presidio_analyzer
    if _presidio_analyzer is None or _presidio_analyzer.language != language:
        _presidio_analyzer = PresidioTextAnalyzer(
            language=language, preferred_model_size=preferred_model_size
        )
    return _presidio_analyzer


def presidio_analyze_text_column(
    column_data: pd.Series,
    confidence_threshold: float = 0.7,
    sample_size: int = 100,
) -> dict[str, Any]:
    """Analyze text column with Presidio.

    Args:
        column_data: Pandas Series with text data
        confidence_threshold: Minimum confidence for detections
        sample_size: Maximum samples to analyze

    Returns:
        Analysis results dictionary

    """
    analyzer = get_presidio_analyzer()
    return analyzer.analyze_column_text(
        column_data, confidence_threshold=confidence_threshold, sample_size=sample_size
    )


def presidio_anonymize_text_column(
    column_data: pd.Series, operators: dict[str, Any] | None = None
) -> pd.Series:
    """Anonymize text column with Presidio.

    Args:
        column_data: Pandas Series with text data
        operators: Custom anonymization operators

    Returns:
        Anonymized pandas Series

    """
    analyzer = get_presidio_analyzer()

    if not analyzer.is_available():
        logger.warning("Presidio not available, returning original column")
        return column_data

    def anonymize_single_text(text):
        if isinstance(text, str) and len(text.strip()) > 0:
            return analyzer.anonymize_text(text, operators=operators)
        return text

    return column_data.apply(anonymize_single_text)


def presidio_analyze_dataframe_batch(
    dataframe: pd.DataFrame,
    text_columns: list[str] | None = None,
    confidence_threshold: float = 0.7,
    sample_size: int = 100,
    batch_size: int | None = None,
) -> dict[str, dict[str, Any]]:
    """Analyze multiple columns in a DataFrame using batch processing.

    Args:
        dataframe: DataFrame to analyze
        text_columns: List of columns to analyze (None = auto-detect object columns)
        confidence_threshold: Minimum confidence for detections
        sample_size: Sample size per column
        batch_size: Batch size for processing

    Returns:
        Dictionary mapping column names to analysis results

    """
    analyzer = get_presidio_analyzer()

    if not analyzer.is_available():
        logger.warning("Presidio not available")
        return {}

    # Auto-detect text columns if not specified
    if text_columns is None:
        text_columns = [
            col for col in dataframe.columns if dataframe[col].dtype == "object"
        ]

    results = {}
    for col in text_columns:
        if col in dataframe.columns:
            try:
                result = analyzer.analyze_column_text(
                    dataframe[col],
                    confidence_threshold=confidence_threshold,
                    sample_size=sample_size,
                    batch_size=batch_size,
                )
                if result.get("total_detections", 0) > 0:
                    results[col] = result
            except Exception as e:
                logger.error(f"Error analyzing column {col}: {e}")

    return results


def presidio_anonymize_dataframe_batch(
    dataframe: pd.DataFrame,
    columns_to_anonymize: list[str] | None = None,
    operators: dict[str, dict[str, Any]] | None = None,
) -> pd.DataFrame:
    """Anonymize multiple columns in a DataFrame.

    Args:
        dataframe: DataFrame to anonymize
        columns_to_anonymize: List of columns to anonymize
        operators: Dictionary mapping column names to operator configs

    Returns:
        DataFrame with anonymized columns

    """
    analyzer = get_presidio_analyzer()

    if not analyzer.is_available():
        logger.warning("Presidio not available, returning original DataFrame")
        return dataframe

    anonymized_df = dataframe.copy()

    if columns_to_anonymize is None:
        columns_to_anonymize = [
            col for col in dataframe.columns if dataframe[col].dtype == "object"
        ]

    for col in columns_to_anonymize:
        if col in anonymized_df.columns:
            try:
                col_operators = operators.get(col) if operators else None
                anonymized_df[col] = presidio_anonymize_text_column(
                    anonymized_df[col], col_operators
                )
            except Exception as e:
                logger.error(f"Error anonymizing column {col}: {e}")

    return anonymized_df
