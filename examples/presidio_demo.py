"""Demonstration of Presidio integration with PII Detector.

This script shows how to use the new Presidio-enhanced PII detection and anonymization
capabilities. It includes examples of both the basic functionality and the hybrid approach.
"""

import logging

import pandas as pd

# Configure logging to see what's happening
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


def create_sample_dataset():
    """Create a sample dataset with various types of PII for demonstration."""
    data = {
        # Column name-based detection
        "participant_name": [
            "John Smith",
            "Maria Garcia",
            "David Johnson",
            "Sarah Williams",
            "Michael Brown",
        ],
        # Format pattern detection (email)
        "contact_email": [
            "john.smith@gmail.com",
            "maria.garcia@yahoo.com",
            "david.j@company.com",
            "sarah.w@university.edu",
            "m.brown@nonprofit.org",
        ],
        # Format pattern detection (phone)
        "phone_number": [
            "555-123-4567",
            "555-987-6543",
            "555-456-7890",
            "555-234-5678",
            "555-876-5432",
        ],
        # Text content with embedded PII (Presidio's strength)
        "survey_comments": [
            "Please contact me at john.smith@gmail.com if you need more info",
            "My Social Security number is 123-45-6789 for verification",
            "Call me at 555-123-4567 or email maria.garcia@yahoo.com",
            "I live at 123 Main Street, Springfield, IL 62701",
            "You can reach Michael Brown at his office phone 555-876-5432",
        ],
        # Sparsity detection (open-ended responses)
        "detailed_feedback": [
            "The program helped me understand financial planning better",
            "I learned about budgeting and saving through this initiative",
            "This course on entrepreneurship opened new opportunities",
            "The health education sessions were very informative",
            "Training on digital literacy was exactly what I needed",
        ],
        # Non-PII columns
        "age_category": ["25-34", "35-44", "25-34", "45-54", "35-44"],
        "program_rating": [4, 5, 3, 4, 5],
        "completion_status": [
            "completed",
            "completed",
            "partial",
            "completed",
            "completed",
        ],
    }

    return pd.DataFrame(data)


def demo_basic_presidio():
    """Demonstrate basic Presidio functionality."""
    print("\n" + "=" * 60)
    print("BASIC PRESIDIO DEMONSTRATION")
    print("=" * 60)

    from pii_detector.core.presidio_engine import get_presidio_analyzer

    analyzer = get_presidio_analyzer()

    print(f"Presidio Available: {analyzer.is_available()}")

    if analyzer.is_available():
        print(
            f"Supported Entities: {analyzer.get_supported_entities()[:10]}..."
        )  # Show first 10

    # Test text analysis
    test_text = "Contact John Smith at john.smith@email.com or call 555-123-4567. His SSN is 123-45-6789."

    print(f"\nAnalyzing text: '{test_text}'")

    if analyzer.is_available():
        entities = analyzer.analyze_text(test_text, confidence_threshold=0.7)
        print("Detected entities:")
        for entity in entities:
            print(
                f"  - {entity['entity_type']}: '{entity['text']}' (confidence: {entity['score']:.2f})"
            )

        # Anonymize the text
        anonymized = analyzer.anonymize_text(test_text)
        print(f"\nAnonymized text: '{anonymized}'")
    else:
        print("Presidio not available - would use fallback methods")


def demo_unified_detection():
    """Demonstrate unified PII detection combining structural and text analysis."""
    print("\n" + "=" * 60)
    print("UNIFIED DETECTION DEMONSTRATION")
    print("=" * 60)

    from pii_detector.core.unified_processor import UnifiedPIIProcessor

    df = create_sample_dataset()
    print(f"Sample dataset shape: {df.shape}")
    print(f"Columns: {list(df.columns)}")

    # Initialize processor
    processor = UnifiedPIIProcessor()

    # Custom configuration
    config = {
        "use_presidio_detection": True,
        "presidio_confidence_threshold": 0.7,
        "use_column_name_detection": True,
        "use_format_detection": True,
        "use_sparsity_detection": True,
    }

    # Run detection
    print("\nRunning comprehensive PII detection...")
    detection_results = processor.detect_pii_comprehensive(df, detection_config=config)

    # Display results
    print(f"\nDetected PII in {len(detection_results)} columns:")
    for column, result in detection_results.items():
        print(f"\n  Column: {column}")
        print(f"    Method: {result.detection_method}")
        print(f"    Confidence: {result.confidence:.2f}")
        if result.entity_types:
            print(f"    Entity Types: {result.entity_types}")

        # Show some details if available
        if "entities_found" in result.details:
            entities_count = sum(
                len(entities) for entities in result.details["entities_found"].values()
            )
            if entities_count > 0:
                print(f"    Total Detections: {entities_count}")

    # Generate summary
    summary = processor.get_detection_summary(detection_results)
    print("\nDetection Summary:")
    print(f"  Total detections: {summary['total_detections']}")
    print(f"  Average confidence: {summary['average_confidence']:.2f}")
    print(f"  Methods used: {summary['methods_used']}")
    if summary["entity_types_found"]:
        print(f"  Entity types found: {summary['entity_types_found']}")

    return detection_results


def demo_hybrid_anonymization(detection_results):
    """Demonstrate hybrid anonymization using the detection results."""
    print("\n" + "=" * 60)
    print("HYBRID ANONYMIZATION DEMONSTRATION")
    print("=" * 60)

    from pii_detector.core.hybrid_anonymizer import HybridAnonymizer

    df = create_sample_dataset()

    # Initialize anonymizer
    anonymizer = HybridAnonymizer()

    print("Available anonymization methods:")
    methods = anonymizer.get_available_methods()
    for method, info in methods.items():
        print(f"  - {method}: {info['description']}")

    # Custom configuration for specific columns
    anonymization_config = {
        "participant_name": {
            "method": "hash_pseudonymization",
            "prefix": "PARTICIPANT_",
        },
        "contact_email": {"method": "presidio_replace"},
        "survey_comments": {"method": "presidio_replace"},
        "phone_number": {"method": "text_masking"},
    }

    print(f"\nAnonymizing {len(detection_results)} PII columns...")

    # Run anonymization
    anonymized_df, report = anonymizer.anonymize_dataset(
        df, detection_results, anonymization_config
    )

    # Show before/after comparison
    print("\nBEFORE vs AFTER comparison:")
    for column in detection_results:
        if column in df.columns:
            print(f"\n  {column}:")
            print(f"    Original sample: '{df[column].iloc[0]}'")
            print(f"    Anonymized:      '{anonymized_df[column].iloc[0]}'")

    # Show anonymization report
    print("\nAnonymization Report:")
    print(f"  Rows processed: {report['original_shape'][0]}")
    print(f"  Columns processed: {len(report['columns_processed'])}")
    print(f"  Methods applied: {report['methods_applied']}")

    if report.get("text_anonymization"):
        print(
            f"  Text anonymization applied to: {list(report['text_anonymization'].keys())}"
        )

    return anonymized_df


def demo_end_to_end():
    """Demonstrate complete end-to-end workflow."""
    print("\n" + "=" * 60)
    print("END-TO-END WORKFLOW DEMONSTRATION")
    print("=" * 60)

    from pii_detector.core.hybrid_anonymizer import anonymize_dataset_hybrid
    from pii_detector.core.unified_processor import detect_pii_unified

    # Create sample dataset
    df = create_sample_dataset()
    print(f"Starting with dataset: {df.shape}")

    # Step 1: Detect PII
    print("\nStep 1: Detecting PII...")
    pii_results = detect_pii_unified(df, language="en")
    print(f"Found PII in {len(pii_results)} columns")

    # Step 2: Anonymize
    print("\nStep 2: Anonymizing detected PII...")
    anonymized_df, report = anonymize_dataset_hybrid(df, pii_results)

    # Step 3: Verify results
    print("\nStep 3: Verification:")
    print(f"  Original dataset: {df.shape}")
    print(f"  Anonymized dataset: {anonymized_df.shape}")
    print(f"  Data integrity preserved: {df.shape == anonymized_df.shape}")

    # Show data utility metrics
    if "uniqueness_reduction" in report:
        print(f"  Average uniqueness reduction: {report['uniqueness_reduction']:.1f}%")

    print("\nWorkflow completed successfully!")
    return anonymized_df


def main():
    """Run all demonstrations."""
    print("PII Detector with Presidio Integration - Demonstration")
    print("=" * 60)

    try:
        # Demo 1: Basic Presidio functionality
        demo_basic_presidio()

        # Demo 2: Unified detection
        detection_results = demo_unified_detection()

        # Demo 3: Hybrid anonymization
        if detection_results:
            demo_hybrid_anonymization(detection_results)

        # Demo 4: End-to-end workflow
        demo_end_to_end()

        print("\n" + "=" * 60)
        print("ALL DEMONSTRATIONS COMPLETED SUCCESSFULLY!")
        print("=" * 60)

    except Exception as e:
        print(f"\nError during demonstration: {e}")
        print("This might be due to Presidio dependencies not being installed.")
        print("Try running: just install-presidio")


if __name__ == "__main__":
    main()
