#!/usr/bin/env python3
"""Practical examples of batch processing with test data files.

This script demonstrates how to use the batch processing functionality
with the included test data files in tests/data/.

Run this script to see batch processing in action:
    uv run python examples/run_batch_examples.py
"""

import sys
import time
from pathlib import Path

# Add src to path for imports
sys.path.append(str(Path(__file__).parent.parent / "src"))

import pandas as pd

from pii_detector.core.batch_processor import BatchPIIProcessor, process_dataset_batch
from pii_detector.core.presidio_engine import (
    presidio_analyze_dataframe_batch,
    presidio_anonymize_dataframe_batch,
)


def example_1_basic_batch_processing():
    """Run example 1: Basic batch processing with comprehensive test data."""
    print("=" * 60)
    print("EXAMPLE 1: Basic Batch Processing")
    print("=" * 60)

    # Load comprehensive test data
    data_file = Path(__file__).parent.parent / "tests/data/comprehensive_pii_data.csv"

    if not data_file.exists():
        print(f"Test data file not found: {data_file}")
        print("Please ensure you're running from the project root directory.")
        return

    print(f"Loading dataset: {data_file.name}")
    dataset = pd.read_csv(data_file)
    print(f"Dataset shape: {dataset.shape}")
    print(f"Columns: {list(dataset.columns)}")

    # Initialize batch processor
    processor = BatchPIIProcessor(
        chunk_size=10,  # Small chunks for demo
        max_workers=2,  # Limit workers for demo
    )

    print(f"\nProcessing strategy: {processor.get_processing_strategy(dataset)}")

    # Run batch detection
    print("\nRunning batch PII detection...")
    start_time = time.time()

    results = processor.detect_pii_batch(dataset)

    detection_time = time.time() - start_time
    print(f"Detection completed in {detection_time:.2f} seconds")

    print(f"\nFound PII in {len(results)} columns:")
    print("-" * 50)
    for column, result in results.items():
        entity_info = (
            f" ({', '.join(result.entity_types)})" if result.entity_types else ""
        )
        print(
            f"{column:<20} | {result.detection_method:<25} | {result.confidence:.2f}{entity_info}"
        )

    print("\nHigh confidence detections (>0.8):")
    high_conf = {col: res for col, res in results.items() if res.confidence > 0.8}
    for col in high_conf:
        print(f"  - {col}")


def example_2_complete_workflow():
    """Run example 2: Complete detection and anonymization workflow."""
    print("\n" + "=" * 60)
    print("EXAMPLE 2: Complete Batch Workflow")
    print("=" * 60)

    data_file = Path(__file__).parent.parent / "tests/data/sample_pii_data.csv"

    if not data_file.exists():
        print(f"Test data file not found: {data_file}")
        return

    print(f"Loading dataset: {data_file.name}")
    dataset = pd.read_csv(data_file)

    # Progress tracking function
    def show_progress(percent, message):
        print(f"  Progress: {percent:5.1f}% - {message}")

    print("\nRunning complete batch processing workflow...")
    print("This includes both detection and anonymization phases:")

    start_time = time.time()

    # Run complete workflow
    detection_results, anonymized_dataset, report = process_dataset_batch(
        dataset,
        language="en",
        chunk_size=5,  # Small chunks for demo
        max_workers=2,
        progress_callback=show_progress,
    )

    total_time = time.time() - start_time

    print(f"\nWorkflow completed in {total_time:.2f} seconds")
    print(f"\nDetected PII in {len(detection_results)} columns:")
    for col, result in detection_results.items():
        print(
            f"  - {col}: {result.detection_method} (confidence: {result.confidence:.2f})"
        )

    print("\nAnonymization report:")
    print(f"  - Original shape: {report.get('original_shape', 'N/A')}")
    print(f"  - Final shape: {report.get('final_shape', 'N/A')}")
    print(f"  - Columns processed: {len(report.get('columns_processed', []))}")

    # Show sample of anonymized data
    print("\nSample of anonymized data (first 3 rows):")
    print(anonymized_dataset.head(3).to_string(index=False))


def example_3_presidio_dataframe_functions():
    """Run example 3: DataFrame-level Presidio functions."""
    print("\n" + "=" * 60)
    print("EXAMPLE 3: Presidio DataFrame Functions")
    print("=" * 60)

    data_file = Path(__file__).parent.parent / "tests/data/comprehensive_pii_data.csv"

    if not data_file.exists():
        print(f"Test data file not found: {data_file}")
        return

    dataset = pd.read_csv(data_file)
    print(f"Loaded dataset with {len(dataset)} rows")

    # Focus on text-rich columns
    text_columns = ["full_name", "notes", "address"]
    print(f"\nAnalyzing text columns: {text_columns}")

    # Batch Presidio analysis
    print("\nRunning Presidio text analysis...")
    try:
        analysis_results = presidio_analyze_dataframe_batch(
            dataset,
            text_columns=text_columns,
            confidence_threshold=0.6,
            sample_size=len(dataset),  # Analyze all rows
        )

        if analysis_results:
            print("\nPresidio text analysis results:")
            for col, result in analysis_results.items():
                entities = result.get("entities_found", {})
                detections = result.get("total_detections", 0)
                confidence = result.get("average_confidence", 0)
                print(f"  {col}:")
                print(f"    Entities found: {list(entities.keys())}")
                print(f"    Total detections: {detections}")
                print(f"    Average confidence: {confidence:.2f}")

            # Batch anonymization
            print(f"\nAnonymizing {len(analysis_results)} text columns...")
            anonymized_df = presidio_anonymize_dataframe_batch(
                dataset, columns_to_anonymize=list(analysis_results.keys())
            )

            print("\nText anonymization examples:")
            for col in list(analysis_results.keys())[:2]:  # Show first 2 columns
                print(f"\n{col}:")
                print("  Original → Anonymized")
                for i in range(min(3, len(dataset))):  # Show first 3 rows
                    orig = str(dataset[col].iloc[i])
                    anon = str(anonymized_df[col].iloc[i])
                    if orig != anon:  # Only show changed values
                        print(f"  {orig}")
                        print(f"  → {anon}")
                        break
        else:
            print("No PII detected by Presidio in text columns")

    except Exception as e:
        print("Note: Presidio functionality requires 'just install-presidio' first")
        print(f"Error: {e}")


def example_4_multiple_files():
    """Run example 4: Process multiple test files."""
    print("\n" + "=" * 60)
    print("EXAMPLE 4: Batch Processing Multiple Files")
    print("=" * 60)

    test_data_dir = Path(__file__).parent.parent / "tests/data"
    csv_files = list(test_data_dir.glob("*.csv"))

    print(f"Found {len(csv_files)} CSV files in {test_data_dir}")

    processor = BatchPIIProcessor(chunk_size=100)

    for file_path in csv_files:
        print(f"\nProcessing: {file_path.name}")

        try:
            dataset = pd.read_csv(file_path)
            results = processor.detect_pii_batch(dataset)

            print(f"  Dataset shape: {dataset.shape}")
            print(f"  PII columns found: {len(results)}")

            if results:
                pii_columns = list(results.keys())
                if len(pii_columns) <= 5:
                    print(f"  PII columns: {pii_columns}")
                else:
                    print(
                        f"  PII columns: {pii_columns[:5]}... (and {len(pii_columns) - 5} more)"
                    )

                # Show highest confidence detection
                max_conf_col = max(results.items(), key=lambda x: x[1].confidence)
                print(
                    f"  Highest confidence: {max_conf_col[0]} ({max_conf_col[1].confidence:.2f})"
                )
            else:
                print("  No PII detected (clean dataset)")

        except Exception as e:
            print(f"  Error: {e}")


def example_5_performance_comparison():
    """Run example 5: Performance comparison between strategies."""
    print("\n" + "=" * 60)
    print("EXAMPLE 5: Performance Comparison")
    print("=" * 60)

    data_file = Path(__file__).parent.parent / "tests/data/comprehensive_pii_data.csv"

    if not data_file.exists():
        print(f"Test data file not found: {data_file}")
        return

    dataset = pd.read_csv(data_file)

    # Create larger dataset by duplicating rows
    print("Creating larger dataset for performance testing...")
    large_dataset = pd.concat([dataset] * 50, ignore_index=True)  # 50x larger
    print(f"Large dataset shape: {large_dataset.shape}")

    processor = BatchPIIProcessor()

    # Get processing strategy
    strategy = processor.get_processing_strategy(large_dataset)
    print(f"\nRecommended processing strategy: {strategy}")

    # Get time estimates
    estimates = processor.estimate_processing_time(large_dataset)
    print("\nProcessing time estimates:")
    print("-" * 40)
    for strategy_name, estimate in estimates.items():
        recommended = "⭐ RECOMMENDED" if estimate["recommended"] else ""
        print(f"{strategy_name}:")
        print(f"  Time: {estimate['time_seconds']:6.2f} seconds")
        print(f"  Memory: {estimate['memory_mb']:8.1f} MB")
        print(f"  {recommended}")

    # Actually test performance (smaller dataset for demo)
    test_dataset = pd.concat([dataset] * 5, ignore_index=True)  # 5x for actual test
    print(f"\nActual performance test with {test_dataset.shape[0]} rows:")

    # Standard processing
    start_time = time.time()
    processor_standard = BatchPIIProcessor(
        chunk_size=10000
    )  # Large chunk = no chunking
    results_standard = processor_standard.detect_pii_batch(test_dataset)
    time_standard = time.time() - start_time

    # Chunked processing
    start_time = time.time()
    processor_chunked = BatchPIIProcessor(chunk_size=50, max_workers=2)
    results_chunked = processor_chunked.detect_pii_batch(test_dataset)
    time_chunked = time.time() - start_time

    print(
        f"  Standard processing: {time_standard:.2f}s ({len(results_standard)} columns)"
    )
    print(
        f"  Chunked processing:  {time_chunked:.2f}s ({len(results_chunked)} columns)"
    )

    if time_standard > 0:
        efficiency = ((time_standard - time_chunked) / time_standard) * 100
        print(f"  Efficiency change: {efficiency:+.1f}%")


def main():
    """Run all batch processing examples."""
    print("Batch Processing Examples with Test Data")
    print("This script demonstrates the batch processing capabilities")
    print("using the test data files in tests/data/")

    try:
        example_1_basic_batch_processing()
        example_2_complete_workflow()
        example_3_presidio_dataframe_functions()
        example_4_multiple_files()
        example_5_performance_comparison()

        print("\n" + "=" * 60)
        print("ALL EXAMPLES COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        print("\nNext steps:")
        print("• Try modifying the examples with your own data")
        print("• Experiment with different chunk sizes and worker counts")
        print("• Install Presidio for enhanced text analysis: just install-presidio")
        print("• Run the full batch demo: just run-batch-demo")

    except KeyboardInterrupt:
        print("\n\nExample execution interrupted by user.")

    except Exception as e:
        print(f"\nError during example execution: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
