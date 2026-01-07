"""Fixed CLI that doesn't auto-launch GUI."""

import argparse
import sys
from pathlib import Path

# Import batch processing functionality
from pii_detector.core.batch_processor import process_dataset_batch
from pii_detector.core.processor import import_dataset
from pii_detector.gui.frontend import main as gui_main


def main():
    """Run the CLI interface for PII detection."""
    parser = argparse.ArgumentParser(
        description="PII Detector - Identify and handle PII in datasets",
        epilog="Use --help with subcommands for more info",
    )

    # Global options
    parser.add_argument(
        "--version", "-v", action="version", version="PII Detector 0.2.23"
    )
    parser.add_argument("--verbose", action="store_true", help="Verbose output")
    parser.add_argument(
        "--output-format",
        choices=["table", "json", "csv"],
        default="table",
        help="Output format",
    )

    # Subcommands
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # GUI command
    subparsers.add_parser("gui", help="Launch graphical interface")

    # Analyze command
    analyze_parser = subparsers.add_parser("analyze", help="Analyze file for PII")
    analyze_parser.add_argument("file", help="Path to dataset file")
    analyze_parser.add_argument(
        "--presidio", action="store_true", help="Enable Presidio ML detection"
    )
    analyze_parser.add_argument(
        "--no-location", action="store_true", help="Disable location population checks"
    )
    analyze_parser.add_argument(
        "--confidence", type=float, default=0.7, help="Confidence threshold (0.0-1.0)"
    )

    # Batch command
    batch_parser = subparsers.add_parser("batch", help="Batch process multiple files")
    batch_parser.add_argument("pattern", help="File pattern (e.g., '*.csv')")
    batch_parser.add_argument(
        "--chunk-size", type=int, default=1000, help="Processing chunk size"
    )
    batch_parser.add_argument(
        "--workers", type=int, default=4, help="Number of parallel workers"
    )

    # Anonymize command
    anon_parser = subparsers.add_parser("anonymize", help="Anonymize dataset")
    anon_parser.add_argument("file", help="Path to dataset file")
    anon_parser.add_argument("--output", "-o", help="Output file path")
    anon_parser.add_argument(
        "--method",
        choices=["hash", "remove", "presidio"],
        default="hash",
        help="Anonymization method",
    )

    args = parser.parse_args()

    # Route to appropriate handler
    if args.command == "gui" or args.command is None:
        # Only launch GUI if explicitly requested or no command given
        if args.command is None:
            print(
                "No command specified. Available commands: analyze, batch, anonymize, gui"
            )
            print(
                "Use --help for more information, or 'gui' to launch the graphical interface."
            )
            return 1
        gui_main()

    elif args.command == "analyze":
        return handle_analyze_command(args)

    elif args.command == "batch":
        return handle_batch_command(args)

    elif args.command == "anonymize":
        return handle_anonymize_command(args)

    else:
        parser.print_help()
        return 1

    return 0


def handle_analyze_command(args):
    """Handle the analyze command."""
    file_path = Path(args.file)
    if not file_path.exists():
        print(f"Error: File '{file_path}' not found.")
        return 1

    print(f"Analyzing file: {file_path}")

    # Load dataset
    success, result = import_dataset(str(file_path))
    if not success:
        print(f"Error loading dataset: {result}")
        return 1

    dataset, dataset_path, label_dict, value_label_dict = result
    print(f"Loaded dataset: {len(dataset)} rows, {len(dataset.columns)} columns")

    # Configure detection
    detection_config = {
        "use_presidio_detection": args.presidio,
        "use_location_detection": not args.no_location,
        "presidio_confidence_threshold": args.confidence,
    }

    # Run detection (using basic unified processor for now)
    from pii_detector.core.unified_processor import detect_pii_unified

    results = detect_pii_unified(dataset, label_dict, config=detection_config)

    # Output results
    print_results(results, args.output_format)
    return 0


def handle_batch_command(args):
    """Handle the batch processing command."""
    import glob

    files = glob.glob(args.pattern)
    if not files:
        print(f"No files found matching pattern: {args.pattern}")
        return 1

    print(f"Processing {len(files)} files with batch processing...")

    for file_path in files:
        print(f"Processing: {file_path}")

        # Load and process each file
        success, result = import_dataset(file_path)
        if success:
            dataset, _, label_dict, _ = result

            # Use batch processor
            detection_results, anonymized_df, report = process_dataset_batch(
                dataset,
                label_dict=label_dict,
                chunk_size=args.chunk_size,
                max_workers=args.workers,
            )

            print(f"  Found PII in {len(detection_results)} columns")
            print(f"  Processing completed: {report.get('batch_anonymization', 'No')}")
        else:
            print(f"  Error: {result}")

    return 0


def handle_anonymize_command(args):
    """Handle the anonymize command."""
    file_path = Path(args.file)
    if not file_path.exists():
        print(f"Error: File '{file_path}' not found.")
        return 1

    # Determine output path
    if args.output:
        output_path = Path(args.output)
    else:
        output_path = (
            file_path.parent / f"{file_path.stem}_anonymized{file_path.suffix}"
        )

    print(f"Anonymizing: {file_path} -> {output_path}")

    # Load dataset
    success, result = import_dataset(str(file_path))
    if not success:
        print(f"Error loading dataset: {result}")
        return 1

    dataset, _, label_dict, _ = result

    # Detect PII first
    from pii_detector.core.unified_processor import detect_pii_unified

    detection_results = detect_pii_unified(dataset, label_dict)

    if not detection_results:
        print("No PII detected - nothing to anonymize")
        return 0

    # Anonymize using hybrid anonymizer
    from pii_detector.core.hybrid_anonymizer import anonymize_dataset_hybrid

    anonymization_config = {col: {"method": args.method} for col in detection_results}

    anonymized_df, report = anonymize_dataset_hybrid(
        dataset, detection_results, anonymization_config
    )

    # Save results
    if output_path.suffix.lower() == ".csv":
        anonymized_df.to_csv(output_path, index=False)
    elif output_path.suffix.lower() in [".xlsx", ".xls"]:
        anonymized_df.to_excel(output_path, index=False)
    else:
        # Default to CSV
        anonymized_df.to_csv(output_path, index=False)

    print(f"Anonymized dataset saved to: {output_path}")
    print(f"Processed {len(report.get('columns_processed', []))} PII columns")

    return 0


def print_results(results, output_format):
    """Print detection results in specified format."""
    if output_format == "json":
        import json

        # Convert results to JSON-serializable format
        json_results = {}
        for col, result in results.items():
            json_results[col] = {
                "detection_method": result.detection_method,
                "confidence": result.confidence,
                "entity_types": result.entity_types,
            }
        print(json.dumps(json_results, indent=2))

    elif output_format == "csv":
        print("Column,Detection Method,Confidence,Entity Types")
        for col, result in results.items():
            entity_types = ";".join(result.entity_types) if result.entity_types else ""
            print(
                f"{col},{result.detection_method},{result.confidence:.2f},{entity_types}"
            )

    else:  # table format
        if results:
            print(f"\nFound PII in {len(results)} columns:")
            print("-" * 60)
            for col, result in results.items():
                entity_info = (
                    f" ({', '.join(result.entity_types)})"
                    if result.entity_types
                    else ""
                )
                print(
                    f"{col:25} | {result.detection_method:20} | {result.confidence:.2f}{entity_info}"
                )
        else:
            print("No PII detected in this dataset.")


if __name__ == "__main__":
    sys.exit(main())
