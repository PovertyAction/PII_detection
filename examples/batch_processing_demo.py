#!/usr/bin/env python3
"""Demonstration of efficient batch processing for PII detection and anonymization.

This example shows how to use the new batch processing capabilities for handling
large datasets efficiently with Presidio integration.
"""

import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

# Add src to path for imports
sys.path.append(str(Path(__file__).parent.parent / "src"))

from pii_detector.core.batch_processor import BatchPIIProcessor, process_dataset_batch
from pii_detector.core.presidio_engine import (
    presidio_analyze_dataframe_batch,
    presidio_anonymize_dataframe_batch,
)


def create_sample_dataset(rows: int = 10000) -> pd.DataFrame:
    """Create a synthetic dataset with various PII types for testing."""
    print(f"Creating synthetic dataset with {rows} rows...")

    np.random.seed(42)

    # Generate synthetic data
    names = [
        "John Smith",
        "Jane Doe",
        "Michael Johnson",
        "Sarah Wilson",
        "David Brown",
        "Lisa Davis",
        "Robert Miller",
        "Jennifer Garcia",
    ] * (rows // 8 + 1)

    emails = [f"user{i}@example.com" for i in range(rows)]
    phones = [
        f"555-{np.random.randint(100, 999):03d}-{np.random.randint(1000, 9999):04d}"
        for _ in range(rows)
    ]

    addresses = [
        f"{np.random.randint(100, 9999)} Main St, Springfield, IL",
        f"{np.random.randint(100, 9999)} Oak Ave, Chicago, IL",
        f"{np.random.randint(100, 9999)} First St, Peoria, IL",
    ] * (rows // 3 + 1)

    ssns = [
        f"{np.random.randint(100, 999):03d}-{np.random.randint(10, 99):02d}-{np.random.randint(1000, 9999):04d}"
        for _ in range(rows)
    ]

    # Create DataFrame
    data = {
        "id": range(1, rows + 1),
        "full_name": names[:rows],
        "email_address": emails,
        "phone_number": phones,
        "home_address": addresses[:rows],
        "ssn": ssns,
        "age": np.random.randint(18, 80, rows),
        "salary": np.random.randint(30000, 150000, rows),
        "comments": [
            f"This is a comment from {names[i % len(names)]} with email {emails[i]}"
            for i in range(rows)
        ],
        "survey_response": [
            f"I live at {addresses[i % len(addresses)]} and can be reached at {phones[i]}"
            for i in range(rows)
        ],
    }

    return pd.DataFrame(data)


def demonstrate_batch_detection():
    """Demonstrate batch PII detection capabilities."""
    print("\n" + "=" * 60)
    print("BATCH PII DETECTION DEMONSTRATION")
    print("=" * 60)

    # Create test datasets of different sizes
    datasets = {
        "Small (1K rows)": create_sample_dataset(1000),
        "Medium (5K rows)": create_sample_dataset(5000),
        "Large (10K rows)": create_sample_dataset(10000),
    }

    for name, dataset in datasets.items():
        print(f"\n--- Processing {name} ---")
        print(f"Dataset shape: {dataset.shape}")

        # Initialize batch processor
        processor = BatchPIIProcessor(
            language="en", chunk_size=1000, max_workers=4, use_structured_engine=True
        )

        # Show processing strategy
        strategy = processor.get_processing_strategy(dataset)
        print(f"Processing strategy: {strategy}")

        # Estimate processing time
        estimates = processor.estimate_processing_time(dataset)
        print(
            f"Time estimate: {estimates.get(strategy, {}).get('time_seconds', 0):.2f} seconds"
        )

        # Track progress
        def progress_callback(percent, message):
            print(f"  Progress: {percent:.1f}% - {message}")

        # Perform detection
        start_time = time.time()
        results = processor.detect_pii_batch(
            dataset, progress_callback=progress_callback
        )
        detection_time = time.time() - start_time

        # Show results
        print(f"Detection completed in {detection_time:.2f} seconds")
        print(f"Found PII in {len(results)} columns:")

        for col, result in results.items():
            print(
                f"  - {col}: {result.detection_method} (confidence: {result.confidence:.2f})"
            )
            if result.entity_types:
                print(f"    Entity types: {', '.join(result.entity_types)}")


def demonstrate_batch_anonymization():
    """Demonstrate batch anonymization capabilities."""
    print("\n" + "=" * 60)
    print("BATCH ANONYMIZATION DEMONSTRATION")
    print("=" * 60)

    # Create a medium-sized dataset
    dataset = create_sample_dataset(5000)
    print(f"Original dataset shape: {dataset.shape}")

    # Use the complete batch processing workflow
    def progress_callback(percent, message):
        print(f"Progress: {percent:.1f}% - {message}")

    print("\nRunning complete batch processing workflow...")
    start_time = time.time()

    detection_results, anonymized_dataset, report = process_dataset_batch(
        dataset,
        language="en",
        chunk_size=1000,
        max_workers=4,
        progress_callback=progress_callback,
    )

    total_time = time.time() - start_time

    print(f"\nBatch processing completed in {total_time:.2f} seconds")
    print(f"Processed {len(detection_results)} PII columns")
    print(f"Anonymized dataset shape: {anonymized_dataset.shape}")

    # Show before/after comparison for a few columns
    print("\n--- Before/After Comparison ---")
    pii_columns = list(detection_results.keys())[:3]  # Show first 3 PII columns

    for col in pii_columns:
        if col in dataset.columns:
            print(f"\nColumn: {col}")
            print("Original values (first 3):")
            for val in dataset[col].head(3):
                print(f"  {val}")
            print("Anonymized values (first 3):")
            for val in anonymized_dataset[col].head(3):
                print(f"  {val}")


def demonstrate_presidio_dataframe_functions():
    """Demonstrate new DataFrame-level Presidio functions."""
    print("\n" + "=" * 60)
    print("PRESIDIO DATAFRAME FUNCTIONS DEMONSTRATION")
    print("=" * 60)

    # Create a smaller dataset for detailed analysis
    dataset = create_sample_dataset(1000)
    text_columns = ["full_name", "email_address", "comments", "survey_response"]

    print(f"Analyzing text columns: {text_columns}")

    # Batch analysis
    print("\n--- Batch Analysis ---")
    start_time = time.time()
    analysis_results = presidio_analyze_dataframe_batch(
        dataset,
        text_columns=text_columns,
        confidence_threshold=0.6,
        sample_size=50,
        batch_size=10,
    )
    analysis_time = time.time() - start_time

    print(f"Analysis completed in {analysis_time:.2f} seconds")
    print(f"Found PII in {len(analysis_results)} columns:")

    for col, result in analysis_results.items():
        entities = result.get("entities_found", {})
        total_detections = result.get("total_detections", 0)
        avg_confidence = result.get("average_confidence", 0)

        print(f"\n  {col}:")
        print(f"    Total detections: {total_detections}")
        print(f"    Average confidence: {avg_confidence:.2f}")
        print(f"    Entity types found: {list(entities.keys())}")

    # Batch anonymization
    print("\n--- Batch Anonymization ---")
    columns_to_anonymize = list(analysis_results.keys())

    start_time = time.time()
    anonymized_df = presidio_anonymize_dataframe_batch(
        dataset, columns_to_anonymize=columns_to_anonymize
    )
    anonymization_time = time.time() - start_time

    print(f"Anonymization completed in {anonymization_time:.2f} seconds")

    # Show examples
    print("\n--- Anonymization Examples ---")
    for col in columns_to_anonymize[:2]:  # Show first 2 columns
        print(f"\nColumn: {col}")
        print("Original → Anonymized")
        for orig, anon in zip(dataset[col].head(3), anonymized_df[col].head(3)):
            print(f"  {orig}")
            print(f"  → {anon}")
            print()


def demonstrate_performance_comparison():
    """Compare performance between different processing approaches."""
    print("\n" + "=" * 60)
    print("PERFORMANCE COMPARISON")
    print("=" * 60)

    dataset = create_sample_dataset(2000)

    # Standard processing
    print("\n--- Standard Processing ---")
    start_time = time.time()
    processor_standard = BatchPIIProcessor(
        chunk_size=10000
    )  # Large chunk = no chunking
    results_standard = processor_standard.detect_pii_batch(dataset)
    time_standard = time.time() - start_time

    print(f"Standard processing: {time_standard:.2f} seconds")
    print(f"Columns detected: {len(results_standard)}")

    # Chunked processing
    print("\n--- Chunked Processing ---")
    start_time = time.time()
    processor_chunked = BatchPIIProcessor(chunk_size=500, max_workers=4)
    results_chunked = processor_chunked.detect_pii_batch(dataset)
    time_chunked = time.time() - start_time

    print(f"Chunked processing: {time_chunked:.2f} seconds")
    print(f"Columns detected: {len(results_chunked)}")

    # Show efficiency
    if time_standard > 0:
        efficiency = ((time_standard - time_chunked) / time_standard) * 100
        print(f"\nEfficiency improvement: {efficiency:.1f}%")


def main():
    """Run main demonstration for PII detection batch processing."""
    print("Batch Processing Demo for PII Detection")
    print("This demo showcases efficient processing of large datasets")

    try:
        demonstrate_batch_detection()
        demonstrate_batch_anonymization()
        demonstrate_presidio_dataframe_functions()
        demonstrate_performance_comparison()

        print("\n" + "=" * 60)
        print("DEMO COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        print("\nKey features demonstrated:")
        print("✓ Batch PII detection with multiple strategies")
        print("✓ Efficient chunked processing for large datasets")
        print("✓ Parallel processing with configurable workers")
        print("✓ Integrated Presidio text analysis")
        print("✓ Complete anonymization workflow")
        print("✓ Performance optimization techniques")

    except Exception as e:
        print(f"\nError during demonstration: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
