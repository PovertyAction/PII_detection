"""Backend integration adapter for Flet GUI.

This module provides a bridge between the Flet GUI and the existing PII detection
core modules, handling the conversion between GUI state and backend processing.
"""

import os
import threading
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pandas as pd

from pii_detector.core import processor
from pii_detector.core.anonymization import AnonymizationTechniques
from pii_detector.core.unified_processor import detect_pii_unified
from pii_detector.gui.flet_app.config.settings import (
    DetectionConfig,
    DetectionResult,
)


class PIIDetectionAdapter:
    """Adapter class to connect Flet GUI with PII detection backend."""

    def __init__(self):
        """Initialize the PII detection adapter."""
        self.anonymizer = AnonymizationTechniques()
        self.current_dataset = None
        self.current_label_dict = None
        self.detection_results = None

    def convert_gui_config_to_backend_config(
        self, detection_config: DetectionConfig, api_key: str | None = None
    ) -> dict[str, Any]:
        """Convert GUI detection configuration to backend configuration format.

        Args:
            detection_config: GUI detection configuration
            api_key: Optional GeoNames API key for location checks

        Returns:
            Dictionary with backend configuration parameters

        """
        config = {
            # Method enable/disable flags
            "use_column_name_detection": detection_config.column_name_enabled,
            "use_format_pattern_detection": detection_config.format_pattern_enabled,
            "use_sparsity_detection": detection_config.sparsity_enabled,
            "use_text_analysis": detection_config.ai_text_enabled,
            "use_location_detection": detection_config.location_population_enabled,
            # Method-specific parameters
            "confidence_threshold": detection_config.confidence_threshold,
            "language": detection_config.language,
            "sample_size": detection_config.sample_size,
            "chunk_size": detection_config.chunk_size,
            "max_workers": detection_config.max_workers,
            # Sparsity analysis settings
            "sparsity_threshold": detection_config.sparsity_threshold,
            # Location population settings
            "population_threshold": detection_config.population_threshold,
            # Text analysis settings
            "text_analysis_mode": detection_config.text_analysis_mode,
            # API credentials
            "geonames_api_key": api_key,
        }

        return config

    def load_dataset(self, file_path: str) -> tuple[bool, str]:
        """Load a dataset file using the existing backend processor.

        Args:
            file_path: Path to the dataset file

        Returns:
            Tuple of (success, message)

        """
        try:
            success, result = processor.import_dataset(file_path)

            if success:
                self.current_dataset, _, self.current_label_dict, _ = result
                return (
                    True,
                    f"Successfully loaded dataset with {len(self.current_dataset)} rows and {len(self.current_dataset.columns)} columns",
                )
            else:
                return False, f"Failed to load dataset: {result}"

        except Exception as e:
            return False, f"Error loading dataset: {str(e)}"

    def run_pii_detection(
        self,
        detection_config: DetectionConfig,
        api_key: str | None = None,
        progress_callback: Callable[[float, str], None] | None = None,
    ) -> tuple[bool, list[DetectionResult]]:
        """Run PII detection on the loaded dataset.

        Args:
            detection_config: GUI detection configuration
            api_key: Optional GeoNames API key
            progress_callback: Optional callback for progress updates

        Returns:
            Tuple of (success, detection_results)

        """
        if self.current_dataset is None:
            return False, []

        try:
            # Convert GUI config to backend config
            backend_config = self.convert_gui_config_to_backend_config(
                detection_config, api_key
            )

            if progress_callback:
                progress_callback(0.1, "Preparing analysis configuration")

            # Set up environment variables for API access
            if api_key:
                os.environ["GEONAMES_USERNAME"] = api_key

            if progress_callback:
                progress_callback(0.2, "Running PII detection analysis")

            # Run the unified PII detection
            pii_results = detect_pii_unified(
                dataset=self.current_dataset,
                label_dict=self.current_label_dict,
                language=detection_config.language,
                config=backend_config,
            )

            if progress_callback:
                progress_callback(0.8, "Processing detection results")

            # Convert backend results to GUI format
            gui_results = []
            for column_name, pii_result in pii_results.items():
                # Map PII entity types to human-readable format
                pii_type = self._map_entity_types_to_pii_type(pii_result.entity_types)

                detection_result = DetectionResult(
                    column=column_name,
                    method=pii_result.detection_method,
                    confidence=pii_result.confidence,
                    pii_type=pii_type,
                    entity_types=pii_result.entity_types,
                    details=pii_result.details,
                )
                gui_results.append(detection_result)

            self.detection_results = gui_results

            if progress_callback:
                progress_callback(1.0, "Analysis completed successfully")

            return True, gui_results

        except Exception as e:
            if progress_callback:
                progress_callback(0.0, f"Analysis failed: {str(e)}")
            return False, []

    def _map_entity_types_to_pii_type(self, entity_types: list[str]) -> str:
        """Map detected entity types to human-readable PII type.

        Args:
            entity_types: List of detected entity types

        Returns:
            Human-readable PII type description

        """
        if not entity_types:
            return "Personal Information"

        # Priority mapping for common entity types
        type_mapping = {
            "PERSON": "Person Name",
            "EMAIL_ADDRESS": "Email Address",
            "PHONE_NUMBER": "Phone Number",
            "SSN": "Social Security Number",
            "CREDIT_CARD": "Credit Card Number",
            "LOCATION": "Geographic Location",
            "DATE_TIME": "Date/Time Information",
            "IP_ADDRESS": "IP Address",
            "ORGANIZATION": "Organization Name",
            "IDENTIFIER": "Unique Identifier",
        }

        # Return the first recognized type or a generic description
        for entity_type in entity_types:
            if entity_type in type_mapping:
                return type_mapping[entity_type]

        return "Personal Information"

    def generate_anonymized_dataset(
        self,
        user_actions: dict[str, str],
        progress_callback: Callable[[float, str], None] | None = None,
    ) -> tuple[bool, pd.DataFrame | None]:
        """Generate anonymized dataset based on user actions.

        Args:
            user_actions: Dictionary mapping column names to actions (Drop/Encode/Keep)
            progress_callback: Optional callback for progress updates

        Returns:
            Tuple of (success, anonymized_dataframe)

        """
        if self.current_dataset is None:
            return False, None

        try:
            if progress_callback:
                progress_callback(0.1, "Preparing anonymization")

            anonymized_df = self.current_dataset.copy()

            total_actions = len(user_actions)
            for i, (column, action) in enumerate(user_actions.items()):
                if column not in anonymized_df.columns:
                    continue

                progress = 0.2 + (0.7 * i / total_actions)
                if progress_callback:
                    progress_callback(progress, f"Processing column: {column}")

                if action == "Drop":
                    # Remove the column entirely
                    anonymized_df = self.anonymizer.remove_variables(
                        anonymized_df, [column]
                    )

                elif action == "Encode":
                    # Apply pseudonymization/encoding
                    if anonymized_df[column].dtype == "object":
                        # Text-based columns: hash pseudonymization
                        anonymized_df[column] = self.anonymizer.hash_pseudonymization(
                            anonymized_df[column],
                            consistent=True,
                            prefix=f"ANON_{column.upper()}_",
                        )
                    else:
                        # Numeric columns: add noise
                        anonymized_df[column] = self.anonymizer.add_noise(
                            anonymized_df[column],
                            noise_type="gaussian",
                            noise_level=0.1,
                        )

                # "Keep" action: no changes needed

            if progress_callback:
                progress_callback(1.0, "Anonymization completed successfully")

            return True, anonymized_df

        except Exception as e:
            if progress_callback:
                progress_callback(0.0, f"Anonymization failed: {str(e)}")
            return False, None

    def generate_automatic_anonymized_dataset(
        self,
        anonymization_method: str,
        detection_results: list,
        progress_callback: Callable[[float, str], None] | None = None,
    ) -> tuple[bool, pd.DataFrame | None, str]:
        """Generate anonymized dataset automatically using selected method.

        Args:
            anonymization_method: Method to use (remove, encode, categorize, mask)
            detection_results: List of DetectionResult objects
            progress_callback: Optional callback for progress updates

        Returns:
            Tuple of (success, anonymized_dataframe, report_text)

        """
        if self.current_dataset is None:
            return False, None, "No dataset loaded"

        try:
            if progress_callback:
                progress_callback(0.1, "Preparing automatic anonymization")

            anonymized_df = self.current_dataset.copy()
            pii_columns = [result.column for result in detection_results]
            changes_log = []

            if progress_callback:
                progress_callback(
                    0.2,
                    f"Applying '{anonymization_method}' method to {len(pii_columns)} PII columns",
                )

            if anonymization_method == "remove":
                # Remove all PII columns
                if progress_callback:
                    progress_callback(0.3, "Removing PII columns")

                anonymized_df = self.anonymizer.remove_variables(
                    anonymized_df, pii_columns
                )
                changes_log.append(
                    f"Removed {len(pii_columns)} PII columns: {', '.join(pii_columns)}"
                )

            elif anonymization_method == "encode":
                # Hash/pseudonymize all PII columns
                if progress_callback:
                    progress_callback(0.3, "Encoding PII columns")

                for i, column in enumerate(pii_columns):
                    if column not in anonymized_df.columns:
                        continue

                    progress = 0.3 + (0.5 * i / len(pii_columns))
                    if progress_callback:
                        progress_callback(progress, f"Encoding column: {column}")

                    if anonymized_df[column].dtype == "object":
                        # Text-based columns: hash pseudonymization
                        anonymized_df[column] = self.anonymizer.hash_pseudonymization(
                            anonymized_df[column],
                            consistent=True,
                            prefix=f"ANON_{column.upper()}_",
                        )
                        changes_log.append(f"Hashed text column: {column}")
                    else:
                        # Numeric columns: add noise
                        anonymized_df[column] = self.anonymizer.add_noise(
                            anonymized_df[column],
                            noise_type="gaussian",
                            noise_level=0.1,
                        )
                        changes_log.append(f"Added noise to numeric column: {column}")

            elif anonymization_method == "categorize":
                # Intelligently categorize based on column type
                if progress_callback:
                    progress_callback(0.3, "Categorizing PII columns")

                for i, column in enumerate(pii_columns):
                    if column not in anonymized_df.columns:
                        continue

                    progress = 0.3 + (0.5 * i / len(pii_columns))
                    if progress_callback:
                        progress_callback(progress, f"Categorizing column: {column}")

                    # Try to intelligently categorize based on column name and type
                    column_lower = column.lower()

                    if "age" in column_lower and pd.api.types.is_numeric_dtype(
                        anonymized_df[column]
                    ):
                        # Age categorization
                        anonymized_df[column] = self.anonymizer.age_categorization(
                            anonymized_df[column]
                        )
                        changes_log.append(f"Categorized age column: {column}")

                    elif "date" in column_lower or "time" in column_lower:
                        # Date generalization
                        try:
                            anonymized_df[column] = self.anonymizer.date_generalization(
                                pd.to_datetime(anonymized_df[column]),
                                granularity="month",
                            )
                            changes_log.append(
                                f"Generalized date column to month: {column}"
                            )
                        except Exception:
                            # If date conversion fails, just hash it
                            anonymized_df[column] = (
                                self.anonymizer.hash_pseudonymization(
                                    anonymized_df[column],
                                    consistent=True,
                                    prefix=f"ANON_{column.upper()}_",
                                )
                            )
                            changes_log.append(
                                f"Hashed column (date conversion failed): {column}"
                            )

                    elif (
                        "location" in column_lower
                        or "address" in column_lower
                        or "city" in column_lower
                        or "state" in column_lower
                    ):
                        # Geographic generalization
                        anonymized_df[column] = (
                            self.anonymizer.geographic_generalization(
                                anonymized_df[column], level="state"
                            )
                        )
                        changes_log.append(
                            f"Generalized location to state level: {column}"
                        )

                    else:
                        # Default: hash for text, add noise for numeric
                        if anonymized_df[column].dtype == "object":
                            anonymized_df[column] = (
                                self.anonymizer.hash_pseudonymization(
                                    anonymized_df[column],
                                    consistent=True,
                                    prefix=f"ANON_{column.upper()}_",
                                )
                            )
                            changes_log.append(f"Hashed column: {column}")
                        else:
                            anonymized_df[column] = self.anonymizer.add_noise(
                                anonymized_df[column],
                                noise_type="gaussian",
                                noise_level=0.1,
                            )
                            changes_log.append(f"Added noise to column: {column}")

            elif anonymization_method == "mask":
                # Pattern-based masking
                if progress_callback:
                    progress_callback(0.3, "Masking PII columns")

                for i, column in enumerate(pii_columns):
                    if column not in anonymized_df.columns:
                        continue

                    progress = 0.3 + (0.5 * i / len(pii_columns))
                    if progress_callback:
                        progress_callback(progress, f"Masking column: {column}")

                    if anonymized_df[column].dtype == "object":
                        # Text masking with pattern detection
                        anonymized_df[column] = self.anonymizer.text_masking(
                            anonymized_df[column]
                        )
                        changes_log.append(f"Masked text patterns in column: {column}")
                    else:
                        # For numeric, convert to string and mask
                        anonymized_df[column] = anonymized_df[column].apply(
                            lambda x: "***" if pd.notna(x) else x
                        )
                        changes_log.append(f"Masked numeric column: {column}")

            if progress_callback:
                progress_callback(0.9, "Generating anonymization report")

            # Generate report
            report = self._generate_anonymization_report(
                anonymization_method,
                pii_columns,
                changes_log,
                len(anonymized_df),
                len(anonymized_df.columns),
            )

            if progress_callback:
                progress_callback(1.0, "Anonymization completed successfully")

            return True, anonymized_df, report

        except Exception as e:
            if progress_callback:
                progress_callback(0.0, f"Anonymization failed: {str(e)}")
            return False, None, f"Anonymization failed: {str(e)}"

    def _generate_anonymization_report(
        self,
        method: str,
        pii_columns: list[str],
        changes_log: list[str],
        num_rows: int,
        num_columns: int,
    ) -> str:
        """Generate a report documenting the anonymization process."""
        report_lines = [
            "=" * 70,
            "AUTOMATIC ANONYMIZATION REPORT",
            "=" * 70,
            "",
            f"Anonymization Method: {method.upper()}",
            f"Timestamp: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "DATASET INFORMATION",
            "-" * 70,
            f"Total rows: {num_rows:,}",
            f"Total columns: {num_columns}",
            f"PII columns processed: {len(pii_columns)}",
            "",
            "CHANGES APPLIED",
            "-" * 70,
        ]

        for change in changes_log:
            report_lines.append(f"• {change}")

        report_lines.extend(
            [
                "",
                "AFFECTED COLUMNS",
                "-" * 70,
                ", ".join(pii_columns),
                "",
                "=" * 70,
                "End of Report",
                "=" * 70,
            ]
        )

        return "\n".join(report_lines)

    def save_results(
        self, anonymized_df: pd.DataFrame, output_path: str
    ) -> tuple[bool, str]:
        """Save the anonymized dataset and analysis report.

        Args:
            anonymized_df: The anonymized dataset
            output_path: Directory to save results

        Returns:
            Tuple of (success, message)

        """
        try:
            output_dir = Path(output_path)
            output_dir.mkdir(parents=True, exist_ok=True)

            # Save anonymized dataset
            dataset_path = output_dir / "anonymized_dataset.csv"
            anonymized_df.to_csv(dataset_path, index=False)

            # Generate and save analysis report
            report_path = output_dir / "pii_detection_report.txt"
            self._generate_analysis_report(report_path)

            return True, f"Results saved successfully to {output_dir}"

        except Exception as e:
            return False, f"Failed to save results: {str(e)}"

    def _generate_analysis_report(self, report_path: Path):
        """Generate a text report of the PII detection analysis."""
        with open(report_path, "w") as f:
            f.write("PII Detection Analysis Report\n")
            f.write("=" * 50 + "\n\n")

            if self.current_dataset is not None:
                f.write("Dataset Information:\n")
                f.write(f"  - Total rows: {len(self.current_dataset):,}\n")
                f.write(f"  - Total columns: {len(self.current_dataset.columns):,}\n\n")

            if self.detection_results:
                f.write("PII Detection Results:\n")
                f.write(
                    f"  - Columns flagged as PII: {len(self.detection_results)}\n\n"
                )

                for result in self.detection_results:
                    f.write(f"Column: {result.column}\n")
                    f.write(f"  - Detection Method: {result.method}\n")
                    f.write(f"  - Confidence: {result.confidence:.2%}\n")
                    f.write(f"  - PII Type: {result.pii_type}\n")
                    if result.entity_types:
                        f.write(f"  - Entity Types: {', '.join(result.entity_types)}\n")
                    f.write("\n")

            f.write("Analysis completed successfully.\n")

    def generate_per_column_anonymized_dataset(
        self,
        column_methods: dict[str, str],
        detection_results: list,
        progress_callback: Callable[[float, str], None] | None = None,
    ) -> tuple[bool, pd.DataFrame | None, str]:
        """Generate anonymized dataset with per-column anonymization methods.

        Args:
            column_methods: Dict mapping column_name -> method (remove/encode/categorize/mask/unchanged)
            detection_results: List of DetectionResult objects
            progress_callback: Optional callback for progress updates

        Returns:
            Tuple of (success, anonymized_dataframe, report_text)

        """
        if self.current_dataset is None:
            return False, None, "No dataset loaded"

        try:
            if progress_callback:
                progress_callback(0.1, "Preparing per-column anonymization")

            anonymized_df = self.current_dataset.copy()
            changes_log = []
            pii_columns = [result.column for result in detection_results]

            # Group columns by method for efficient processing
            method_groups = {}
            for column in pii_columns:
                method = column_methods.get(column, "remove")
                if method not in method_groups:
                    method_groups[method] = []
                method_groups[method].append(column)

            total_columns = len(pii_columns)
            processed = 0

            # Process each method group
            for method, columns in method_groups.items():
                if progress_callback:
                    progress_callback(
                        0.2 + (0.7 * processed / total_columns),
                        f"Applying '{method}' to {len(columns)} columns",
                    )

                if method == "unchanged":
                    # Skip these columns - leave them as-is
                    changes_log.append(
                        f"Unchanged (preserved original): {', '.join(columns)}"
                    )

                elif method == "remove":
                    anonymized_df = self.anonymizer.remove_variables(
                        anonymized_df, columns
                    )
                    changes_log.append(f"Removed columns: {', '.join(columns)}")

                elif method == "encode":
                    for column in columns:
                        if column not in anonymized_df.columns:
                            continue
                        if anonymized_df[column].dtype == "object":
                            anonymized_df[column] = (
                                self.anonymizer.hash_pseudonymization(
                                    anonymized_df[column],
                                    consistent=True,
                                    prefix=f"ANON_{column.upper()}_",
                                )
                            )
                            changes_log.append(f"Hashed: {column}")
                        else:
                            anonymized_df[column] = self.anonymizer.add_noise(
                                anonymized_df[column],
                                noise_type="gaussian",
                                noise_level=0.1,
                            )
                            changes_log.append(f"Added noise: {column}")

                elif method == "categorize":
                    for column in columns:
                        if column not in anonymized_df.columns:
                            continue
                        column_lower = column.lower()

                        # Intelligent categorization based on column patterns
                        if "age" in column_lower:
                            anonymized_df[column] = self.anonymizer.age_categorization(
                                anonymized_df[column]
                            )
                            changes_log.append(f"Age categorization: {column}")
                        elif (
                            "date" in column_lower
                            or "time" in column_lower
                            or "dob" in column_lower
                        ):
                            try:
                                anonymized_df[column] = (
                                    self.anonymizer.date_generalization(
                                        pd.to_datetime(
                                            anonymized_df[column], errors="coerce"
                                        ),
                                        granularity="month",
                                    )
                                )
                                changes_log.append(f"Date generalization: {column}")
                            except Exception:
                                # Fallback to top/bottom coding
                                anonymized_df[column] = (
                                    self.anonymizer.top_bottom_coding(
                                        anonymized_df[column]
                                    )
                                )
                                changes_log.append(
                                    f"Top/bottom coding (date conversion failed): {column}"
                                )
                        elif any(
                            keyword in column_lower
                            for keyword in [
                                "location",
                                "address",
                                "city",
                                "state",
                                "zip",
                            ]
                        ):
                            anonymized_df[column] = (
                                self.anonymizer.geographic_generalization(
                                    anonymized_df[column], level="state"
                                )
                            )
                            changes_log.append(f"Geographic generalization: {column}")
                        elif any(
                            keyword in column_lower
                            for keyword in ["income", "salary", "wage", "earnings"]
                        ):
                            anonymized_df[column] = self.anonymizer.income_bracketing(
                                anonymized_df[column]
                            )
                            changes_log.append(f"Income bracketing: {column}")
                        else:
                            # Default to top/bottom coding for numeric, or generic categorization
                            if pd.api.types.is_numeric_dtype(anonymized_df[column]):
                                anonymized_df[column] = (
                                    self.anonymizer.top_bottom_coding(
                                        anonymized_df[column]
                                    )
                                )
                                changes_log.append(f"Top/bottom coding: {column}")
                            else:
                                # For non-numeric, hash it
                                anonymized_df[column] = (
                                    self.anonymizer.hash_pseudonymization(
                                        anonymized_df[column],
                                        consistent=True,
                                        prefix=f"CAT_{column.upper()}_",
                                    )
                                )
                                changes_log.append(
                                    f"Pseudonymization (non-numeric): {column}"
                                )

                elif method == "mask":
                    for column in columns:
                        if column not in anonymized_df.columns:
                            continue
                        if anonymized_df[column].dtype == "object":
                            # Apply text masking to each value in the column
                            anonymized_df[column] = anonymized_df[column].apply(
                                lambda x: self.anonymizer.text_masking(x)
                                if pd.notna(x)
                                else x
                            )
                            changes_log.append(f"Text masking: {column}")
                        else:
                            # Mask numeric values with placeholder
                            anonymized_df[column] = anonymized_df[column].apply(
                                lambda x: "***" if pd.notna(x) else x
                            )
                            changes_log.append(f"Value masking: {column}")

                processed += len(columns)

            if progress_callback:
                progress_callback(0.9, "Generating anonymization report")

            # Generate report
            report = self._generate_per_column_anonymization_report(
                column_methods,
                pii_columns,
                changes_log,
                len(anonymized_df),
                len(anonymized_df.columns),
            )

            if progress_callback:
                progress_callback(1.0, "Anonymization completed successfully")

            return True, anonymized_df, report

        except Exception as e:
            error_msg = f"Anonymization failed: {str(e)}"
            if progress_callback:
                progress_callback(0.0, error_msg)
            return False, None, error_msg

    def _generate_per_column_anonymization_report(
        self,
        column_methods: dict[str, str],
        pii_columns: list[str],
        changes_log: list[str],
        num_rows: int,
        num_columns: int,
    ) -> str:
        """Generate a detailed report documenting per-column anonymization.

        Args:
            column_methods: Dict mapping column names to anonymization methods
            pii_columns: List of PII column names processed
            changes_log: List of change descriptions
            num_rows: Number of rows in dataset
            num_columns: Total number of columns in dataset

        Returns:
            Formatted report text

        """
        import pandas as pd

        # Group by method for summary
        method_counts = {}
        for method in column_methods.values():
            method_counts[method] = method_counts.get(method, 0) + 1

        report_lines = [
            "=" * 70,
            "PER-COLUMN ANONYMIZATION REPORT",
            "=" * 70,
            "",
            f"Timestamp: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "DATASET INFORMATION",
            "-" * 70,
            f"Total rows: {num_rows:,}",
            f"Total columns: {num_columns}",
            f"PII columns processed: {len(pii_columns)}",
            "",
            "METHOD SUMMARY",
            "-" * 70,
        ]

        for method, count in sorted(method_counts.items()):
            report_lines.append(f"  {method.upper()}: {count} columns")

        report_lines.extend(
            [
                "",
                "PER-COLUMN METHODS",
                "-" * 70,
            ]
        )

        for column in sorted(pii_columns):
            method = column_methods.get(column, "unknown")
            report_lines.append(f"  {column}: {method}")

        report_lines.extend(
            [
                "",
                "DETAILED CHANGES",
                "-" * 70,
            ]
        )

        for change in changes_log:
            report_lines.append(f"• {change}")

        report_lines.extend(
            [
                "",
                "METHOD DESCRIPTIONS",
                "-" * 70,
                "• UNCHANGED: Preserves original column values (user overrode PII detection)",
                "• REMOVE: Completely deletes PII columns from the dataset",
                "• ENCODE: Applies hashing (text) or noise addition (numeric) to obfuscate values",
                "• CATEGORIZE: Groups values into ranges or categories (age groups, income brackets, etc.)",
                "• MASK: Replaces values with placeholder characters while preserving format",
                "",
                "=" * 70,
                "End of Report",
                "=" * 70,
            ]
        )

        return "\n".join(report_lines)


class BackgroundProcessor:
    """Background processor for running PII detection without blocking the GUI."""

    def __init__(self, adapter: PIIDetectionAdapter):
        """Initialize the background processor.

        Args:
            adapter: PIIDetectionAdapter instance to use for detection

        """
        self.adapter = adapter
        self.is_running = False
        self.is_cancelled = False

    def run_analysis_async(
        self,
        detection_config: DetectionConfig,
        api_key: str | None,
        progress_callback: Callable[[float, str], None] | None = None,
        completion_callback: Callable[[bool, list[DetectionResult]], None]
        | None = None,
    ):
        """Run PII detection analysis in a background thread.

        Args:
            detection_config: GUI detection configuration
            api_key: Optional GeoNames API key
            progress_callback: Optional callback for progress updates
            completion_callback: Optional callback when analysis completes

        """
        if self.is_running:
            return

        def analysis_thread():
            self.is_running = True
            self.is_cancelled = False

            try:
                success, results = self.adapter.run_pii_detection(
                    detection_config, api_key, progress_callback
                )

                if not self.is_cancelled and completion_callback:
                    completion_callback(success, results)

            except Exception as e:
                if progress_callback:
                    progress_callback(0.0, f"Analysis failed: {str(e)}")
                if completion_callback and not self.is_cancelled:
                    completion_callback(False, [])
            finally:
                self.is_running = False

        thread = threading.Thread(target=analysis_thread, daemon=True)
        thread.start()

    def cancel_analysis(self):
        """Cancel the running analysis."""
        self.is_cancelled = True
        self.is_running = False
