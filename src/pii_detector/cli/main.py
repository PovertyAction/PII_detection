"""Enhanced CLI that provides proper subcommands and batch processing."""

import argparse
import json
import sys
from pathlib import Path

# Import batch processing functionality
from pii_detector.core.batch_processor import BatchPIIProcessor, process_dataset_batch
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
    analyze_parser.add_argument("file", help="Path to dataset file (.csv, .xlsx, .dta)")
    analyze_parser.add_argument(
        "--presidio", action="store_true", help="Enable Presidio ML detection"
    )
    analyze_parser.add_argument(
        "--no-location", action="store_true", help="Disable location population checks"
    )
    analyze_parser.add_argument(
        "--confidence", type=float, default=0.7, help="Confidence threshold (0.0-1.0)"
    )
    analyze_parser.add_argument(
        "--language",
        choices=["en", "es", "other"],
        default="en",
        help="Dataset language",
    )

    # Batch command
    batch_parser = subparsers.add_parser("batch", help="Batch process multiple files")
    batch_parser.add_argument(
        "pattern", help="File pattern (e.g., '*.csv', '*.dta') or directory"
    )
    batch_parser.add_argument(
        "--chunk-size", type=int, default=1000, help="Processing chunk size"
    )
    batch_parser.add_argument(
        "--workers", type=int, default=4, help="Number of parallel workers"
    )
    batch_parser.add_argument(
        "--presidio", action="store_true", help="Enable Presidio ML detection"
    )
    batch_parser.add_argument("--output-dir", help="Directory to save results")

    # Anonymize command
    anon_parser = subparsers.add_parser("anonymize", help="Anonymize dataset")
    anon_parser.add_argument("file", help="Path to dataset file (.csv, .xlsx, .dta)")
    anon_parser.add_argument(
        "--output", "-o", help="Output file path (.csv, .xlsx, .dta)"
    )
    anon_parser.add_argument(
        "--method",
        choices=["hash", "remove", "categorize", "presidio"],
        default="hash",
        help="Anonymization method",
    )
    anon_parser.add_argument(
        "--presidio", action="store_true", help="Enable Presidio ML detection"
    )

    # Report command
    report_parser = subparsers.add_parser(
        "report", help="Generate PII detection report"
    )
    report_parser.add_argument("file", help="Path to dataset file (.csv, .xlsx, .dta)")
    report_parser.add_argument("--output", "-o", help="Report output file")
    report_parser.add_argument(
        "--format", choices=["txt", "json", "html"], default="txt", help="Report format"
    )

    args = parser.parse_args()

    # Route to appropriate handler
    if args.command == "gui":
        gui_main()
    elif args.command == "analyze":
        return handle_analyze_command(args)
    elif args.command == "batch":
        return handle_batch_command(args)
    elif args.command == "anonymize":
        return handle_anonymize_command(args)
    elif args.command == "report":
        return handle_report_command(args)
    elif args.command is None:
        # No command specified - show help and suggest options
        print("PII Detector - Identify and handle PII in datasets")
        print("\nAvailable commands:")
        print("  analyze     Analyze a single file for PII")
        print("  batch       Process multiple files efficiently")
        print("  anonymize   Anonymize detected PII in a dataset")
        print("  report      Generate detailed PII detection reports")
        print("  gui         Launch graphical interface")
        print("\nUse 'pii-detector <command> --help' for command-specific help")
        print("Use 'pii-detector gui' to launch the graphical interface")
        return 0
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

    if args.verbose:
        print(f"Analyzing file: {file_path}")

    # Load dataset
    success, result = import_dataset(str(file_path))
    if not success:
        print(f"Error loading dataset: {result}")
        return 1

    dataset, dataset_path, label_dict, value_label_dict = result
    if args.verbose:
        print(f"Loaded dataset: {len(dataset)} rows, {len(dataset.columns)} columns")

    # Use batch processor for consistent results
    processor = BatchPIIProcessor(
        language=args.language,
        chunk_size=len(dataset),  # Process all at once for single file
        max_workers=1,
    )

    if args.verbose:
        print("Running PII detection...")

    try:
        # Run detection
        results = processor.detect_pii_batch(dataset, label_dict)

        # Output results
        print_results(results, args.output_format, args.verbose)
        return 0

    except Exception as e:
        print(f"Error during analysis: {e}")
        if args.verbose:
            import traceback

            traceback.print_exc()
        return 1


def handle_batch_command(args):
    """Handle the batch processing command."""
    import glob

    # Handle pattern or directory
    if Path(args.pattern).is_dir():
        files = list(Path(args.pattern).glob("*.csv"))
        files.extend(list(Path(args.pattern).glob("*.xlsx")))
        files.extend(list(Path(args.pattern).glob("*.dta")))
        files = [str(f) for f in files]
    else:
        files = glob.glob(args.pattern)

    if not files:
        print(f"No files found matching pattern: {args.pattern}")
        return 1

    print(f"Processing {len(files)} files with batch processing...")

    # Setup output directory
    output_dir = (
        Path(args.output_dir) if args.output_dir else Path.cwd() / "batch_results"
    )
    output_dir.mkdir(exist_ok=True)

    batch_results = {}

    for file_path in files:
        print(f"\nProcessing: {file_path}")

        try:
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
                    language="en",
                )

                batch_results[file_path] = {
                    "pii_columns": len(detection_results),
                    "total_columns": len(dataset.columns),
                    "processing_time": report.get("processing_time_seconds", 0),
                }

                print(
                    f"  Found PII in {len(detection_results)} of {len(dataset.columns)} columns"
                )

                # Save results if output directory specified
                if args.output_dir:
                    file_stem = Path(file_path).stem

                    # Save detection results
                    results_file = output_dir / f"{file_stem}_pii_detection.json"
                    results_data = {
                        col: {
                            "detection_method": result.detection_method,
                            "confidence": result.confidence,
                            "entity_types": result.entity_types,
                        }
                        for col, result in detection_results.items()
                    }
                    with open(results_file, "w") as f:
                        json.dump(results_data, f, indent=2)

                    # Save anonymized dataset in original format when possible
                    original_ext = Path(file_path).suffix.lower()
                    if original_ext == ".dta":
                        anon_file = output_dir / f"{file_stem}_anonymized.dta"
                        try:
                            anonymized_df.to_stata(anon_file, write_index=False)
                        except Exception as e:
                            print(
                                f"    Warning: Could not save as .dta, using CSV: {e}"
                            )
                            anon_file = output_dir / f"{file_stem}_anonymized.csv"
                            anonymized_df.to_csv(anon_file, index=False)
                    elif original_ext in [".xlsx", ".xls"]:
                        anon_file = output_dir / f"{file_stem}_anonymized.xlsx"
                        anonymized_df.to_excel(anon_file, index=False)
                    else:
                        anon_file = output_dir / f"{file_stem}_anonymized.csv"
                        anonymized_df.to_csv(anon_file, index=False)

                    print(f"  Results saved: {results_file}")
                    print(f"  Anonymized data: {anon_file}")

            else:
                print(f"  Error: {result}")
                batch_results[file_path] = {"error": str(result)}

        except Exception as e:
            print(f"  Error processing {file_path}: {e}")
            batch_results[file_path] = {"error": str(e)}

    # Summary
    print(f"\n{'=' * 60}")
    print("BATCH PROCESSING SUMMARY")
    print(f"{'=' * 60}")

    total_files = len(files)
    successful_files = len([r for r in batch_results.values() if "error" not in r])
    total_pii_columns = sum(r.get("pii_columns", 0) for r in batch_results.values())

    print(f"Files processed: {successful_files}/{total_files}")
    print(f"Total PII columns detected: {total_pii_columns}")

    if args.output_dir:
        print(f"Results saved to: {output_dir}")

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

    try:
        # Use batch processor for detection and anonymization
        # First detect PII
        processor = BatchPIIProcessor(language="en")
        detection_results = processor.detect_pii_batch(dataset, label_dict)

        if not detection_results:
            print("No PII detected - nothing to anonymize")
            return 0

        # Then anonymize using the complete workflow
        detection_results, anonymized_df, report = process_dataset_batch(
            dataset,
            label_dict=label_dict,
            language="en",
            anonymization_config={
                col: {"method": args.method} for col in detection_results
            },
        )

        # Save results
        if output_path.suffix.lower() == ".csv":
            anonymized_df.to_csv(output_path, index=False)
        elif output_path.suffix.lower() in [".xlsx", ".xls"]:
            anonymized_df.to_excel(output_path, index=False)
        elif output_path.suffix.lower() == ".dta":
            # Save as Stata format, preserving variable labels if available
            try:
                anonymized_df.to_stata(output_path, write_index=False)
            except Exception as e:
                print(f"Warning: Error saving as .dta format: {e}")
                print("Falling back to CSV format")
                csv_path = output_path.with_suffix(".csv")
                anonymized_df.to_csv(csv_path, index=False)
                print(f"Saved as CSV: {csv_path}")
                return 0
        else:
            # Default to CSV
            anonymized_df.to_csv(output_path, index=False)

        print(f"Anonymized dataset saved to: {output_path}")
        print(f"Processed {len(report.get('columns_processed', []))} PII columns")

        return 0

    except Exception as e:
        print(f"Error during anonymization: {e}")
        return 1


def handle_report_command(args):
    """Handle the report generation command."""
    file_path = Path(args.file)
    if not file_path.exists():
        print(f"Error: File '{file_path}' not found.")
        return 1

    # Determine output path
    if args.output:
        output_path = Path(args.output)
    else:
        extension = ".txt" if args.format == "txt" else f".{args.format}"
        output_path = file_path.parent / f"{file_path.stem}_pii_report{extension}"

    print(f"Generating report: {file_path} -> {output_path}")

    # Load dataset
    success, result = import_dataset(str(file_path))
    if not success:
        print(f"Error loading dataset: {result}")
        return 1

    dataset, _, label_dict, _ = result

    try:
        # Use batch processor for detection
        processor = BatchPIIProcessor(language="en")
        detection_results = processor.detect_pii_batch(dataset, label_dict)

        # Generate report
        if args.format == "json":
            generate_json_report(output_path, file_path, dataset, detection_results)
        elif args.format == "html":
            generate_html_report(output_path, file_path, dataset, detection_results)
        else:  # txt
            generate_text_report(output_path, file_path, dataset, detection_results)

        print(f"Report saved to: {output_path}")
        return 0

    except Exception as e:
        print(f"Error generating report: {e}")
        return 1


def print_results(results, output_format, verbose=False):
    """Print detection results in specified format."""
    if output_format == "json":
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
            print("-" * 70)
            print(
                f"{'Column':<25} | {'Method':<20} | {'Confidence':<10} | {'Entity Types'}"
            )
            print("-" * 70)
            for col, result in results.items():
                entity_info = (
                    ", ".join(result.entity_types) if result.entity_types else "N/A"
                )
                print(
                    f"{col:<25} | {result.detection_method:<20} | {result.confidence:<10.2f} | {entity_info}"
                )
        else:
            print("No PII detected in this dataset.")


def generate_text_report(output_path, file_path, dataset, detection_results):
    """Generate a text format report."""
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("PII Detection Report\n")
        f.write("=" * 60 + "\n\n")
        f.write(f"Dataset: {file_path}\n")
        f.write(f"Rows: {len(dataset)}\n")
        f.write(f"Columns: {len(dataset.columns)}\n\n")

        f.write("Summary:\n")
        f.write(f"  Total columns analyzed: {len(dataset.columns)}\n")
        f.write(f"  Potential PII columns:  {len(detection_results)}\n")
        f.write(
            f"  Clean columns:          {len(dataset.columns) - len(detection_results)}\n\n"
        )

        if detection_results:
            f.write("Detected PII Columns:\n")
            f.write("-" * 40 + "\n")
            for i, (column, result) in enumerate(detection_results.items(), 1):
                entity_types = (
                    ", ".join(result.entity_types) if result.entity_types else "N/A"
                )
                f.write(f"{i:2d}. {column:<25}\n")
                f.write(f"    Method: {result.detection_method}\n")
                f.write(f"    Confidence: {result.confidence:.2f}\n")
                f.write(f"    Entity Types: {entity_types}\n\n")

        f.write("=" * 60 + "\n")
        f.write("Report generated by PII Detector CLI\n")


def generate_json_report(output_path, file_path, dataset, detection_results):
    """Generate a JSON format report."""
    report_data = {
        "dataset": str(file_path),
        "rows": len(dataset),
        "columns": len(dataset.columns),
        "summary": {
            "total_columns": len(dataset.columns),
            "pii_columns": len(detection_results),
            "clean_columns": len(dataset.columns) - len(detection_results),
        },
        "pii_detections": {},
    }

    for col, result in detection_results.items():
        report_data["pii_detections"][col] = {
            "detection_method": result.detection_method,
            "confidence": result.confidence,
            "entity_types": result.entity_types,
        }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(report_data, f, indent=2, ensure_ascii=False)


def generate_html_report(output_path, file_path, dataset, detection_results):
    """Generate an HTML format report."""
    html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>PII Detection Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        h1, h2 {{ color: #333; }}
        table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f2f2f2; }}
        .summary {{ background-color: #f9f9f9; padding: 15px; border-radius: 5px; }}
    </style>
</head>
<body>
    <h1>PII Detection Report</h1>

    <div class="summary">
        <h2>Dataset Information</h2>
        <p><strong>File:</strong> {file_path}</p>
        <p><strong>Rows:</strong> {len(dataset)}</p>
        <p><strong>Columns:</strong> {len(dataset.columns)}</p>
        <p><strong>PII Columns Found:</strong> {len(detection_results)}</p>
        <p><strong>Clean Columns:</strong> {len(dataset.columns) - len(detection_results)}</p>
    </div>

    <h2>Detected PII Columns</h2>
    <table>
        <tr>
            <th>Column Name</th>
            <th>Detection Method</th>
            <th>Confidence</th>
            <th>Entity Types</th>
        </tr>
    """

    for column, result in detection_results.items():
        entity_types = ", ".join(result.entity_types) if result.entity_types else "N/A"
        html_content += f"""
        <tr>
            <td>{column}</td>
            <td>{result.detection_method}</td>
            <td>{result.confidence:.2f}</td>
            <td>{entity_types}</td>
        </tr>
        """

    html_content += """
    </table>
    <p><em>Report generated by PII Detector CLI</em></p>
</body>
</html>
    """

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_content)


if __name__ == "__main__":
    sys.exit(main())
