"""Command-line interface for the PII detector."""

import argparse
import sys
from pathlib import Path

from pii_detector.core.processor import (
    find_piis_based_on_column_format,
    find_piis_based_on_column_name,
    find_piis_based_on_locations_population,
    find_piis_based_on_sparse_entries,
    import_dataset,
)
from pii_detector.data import constants
from pii_detector.gui.frontend import main as gui_main


def main():
    """Run the CLI interface for PII detection."""
    parser = argparse.ArgumentParser(
        description="PII Detector - Identify and handle personally identifiable information in datasets"
    )

    parser.add_argument(
        "--file", "-f", type=str, help="Path to dataset file to analyze"
    )

    parser.add_argument(
        "--gui", "-g", action="store_true", help="Launch the graphical user interface"
    )

    parser.add_argument(
        "--version", "-v", action="version", version="PII Detector 0.2.23"
    )

    args = parser.parse_args()

    if args.gui or len(sys.argv) == 1:
        # Launch GUI if --gui specified or no arguments given
        gui_main()
    elif args.file:
        # Process file via CLI
        file_path = Path(args.file)
        if not file_path.exists():
            print(f"Error: File '{file_path}' not found.")
            return 1

        print(f"Analyzing file: {file_path}")
        success, result = import_dataset(str(file_path))

        if success:
            dataset, dataset_path, label_dict, value_label_dict = result
            print(
                f"Successfully loaded dataset with {len(dataset)} rows and {len(dataset.columns)} columns."
            )
            print("Columns found:", list(dataset.columns))

            # Run PII detection workflow
            run_pii_detection_workflow(
                dataset, dataset_path, label_dict, value_label_dict
            )
        else:
            print(f"Error loading dataset: {result}")
            return 1
    else:
        parser.print_help()
        return 1

    return 0


def run_pii_detection_workflow(dataset, dataset_path, label_dict, value_label_dict):
    """Run the PII detection workflow for CLI."""
    print("\n" + "=" * 50)
    print("🔍 Starting PII Detection Analysis")
    print("=" * 50)

    # Configuration options
    print("\nConfiguration:")
    enable_location_check = get_user_confirmation(
        "Check location populations via API? (may be slow)"
    )
    language = get_language_choice()
    country = get_country_choice() if enable_location_check else "US"

    print(f"Language: {language}")
    print(f"Country: {country}")
    print(
        f"Location population check: {'Enabled' if enable_location_check else 'Disabled'}"
    )

    # Run PII detection algorithms
    all_pii_candidates = []
    print("\n📋 Running PII detection algorithms...")

    # 1. Column name/label matching
    print("  • Checking column names and labels...")
    try:
        column_name_piis = find_piis_based_on_column_name(
            dataset, label_dict or {}, language, country, constants.STRICT
        )
        all_pii_candidates.extend(
            [(col, "Column Name Match") for col in column_name_piis]
        )
        print(f"    Found {len(column_name_piis)} potential PII columns")
    except Exception as e:
        print(f"    Error in column name detection: {e}")

    # 2. Format pattern detection
    print("  • Checking data formats...")
    try:
        format_piis = find_piis_based_on_column_format(dataset)
        all_pii_candidates.extend([(col, "Format Pattern") for col in format_piis])
        print(f"    Found {len(format_piis)} columns with PII patterns")
    except Exception as e:
        print(f"    Error in format detection: {e}")

    # 3. Sparsity analysis
    print("  • Checking for sparse columns...")
    try:
        sparse_piis = find_piis_based_on_sparse_entries(dataset)
        all_pii_candidates.extend([(col, "Sparse Data") for col in sparse_piis])
        print(f"    Found {len(sparse_piis)} sparse columns")
    except Exception as e:
        print(f"    Error in sparsity detection: {e}")

    # 4. Location population check (if enabled)
    if enable_location_check:
        print("  • Checking location populations (this may take a moment)...")
        try:
            location_piis = find_piis_based_on_locations_population(dataset)
            all_pii_candidates.extend(
                [(col, "Small Location") for col in location_piis]
            )
            print(f"    Found {len(location_piis)} small location columns")
        except Exception as e:
            print(f"    Error in location detection: {e}")

    # Process results
    unique_piis = {}
    for col, method in all_pii_candidates:
        if col not in unique_piis:
            unique_piis[col] = [method]
        else:
            unique_piis[col].append(method)

    # Display results
    print("\n" + "=" * 50)
    print("📊 PII Detection Results")
    print("=" * 50)

    if unique_piis:
        print(f"\n🚨 Found {len(unique_piis)} potential PII columns:\n")

        for i, (column, methods) in enumerate(unique_piis.items(), 1):
            methods_text = ", ".join(methods)
            print(f"{i:2d}. {column:<25} → {methods_text}")

        print("\n📈 Summary:")
        print(f"   Total columns analyzed: {len(dataset.columns)}")
        print(f"   Potential PII columns:  {len(unique_piis)}")
        print(f"   Clean columns:          {len(dataset.columns) - len(unique_piis)}")

        # Ask user if they want to save a report
        if get_user_confirmation("\nSave PII detection report to file?"):
            save_pii_report(dataset_path, unique_piis, dataset.columns)

    else:
        print("✅ No PII detected in this dataset.")
        print(
            "   The dataset appears to be clean of obvious personally identifiable information."
        )

    print("\n" + "=" * 50)
    print("Analysis complete!")
    print("=" * 50)


def get_user_confirmation(prompt):
    """Get yes/no confirmation from user."""
    while True:
        response = input(f"{prompt} [y/N]: ").strip().lower()
        if response in ["y", "yes"]:
            return True
        elif response in ["n", "no", ""]:
            return False
        else:
            print("Please enter 'y' for yes or 'n' for no.")


def get_language_choice():
    """Get language choice from user."""
    languages = [constants.ENGLISH, constants.SPANISH, constants.OTHER]
    print("\nAvailable languages:")
    for i, lang in enumerate(languages, 1):
        print(f"  {i}. {lang}")

    while True:
        try:
            choice = input(
                f"Select language [1-{len(languages)}] (default: 1): "
            ).strip()
            if choice == "":
                return languages[0]

            index = int(choice) - 1
            if 0 <= index < len(languages):
                return languages[index]
            else:
                print(f"Please enter a number between 1 and {len(languages)}.")
        except ValueError:
            print("Please enter a valid number.")


def get_country_choice():
    """Get country choice from user."""
    countries = constants.ALL_COUNTRIES[:10]  # Show first 10 countries
    print("\nSelect country (showing top 10 options):")
    for i, country in enumerate(countries, 1):
        print(f"  {i:2d}. {country}")
    print("  11. Other")

    while True:
        try:
            choice = input("Select country [1-11] (default: 1): ").strip()
            if choice == "":
                return countries[0]

            choice_num = int(choice)
            if 1 <= choice_num <= len(countries):
                return countries[choice_num - 1]
            elif choice_num == 11:
                return input("Enter country name: ").strip()
            else:
                print("Please enter a number between 1 and 11.")
        except ValueError:
            print("Please enter a valid number.")


def save_pii_report(dataset_path, unique_piis, all_columns):
    """Save PII detection report to file."""
    try:
        report_path = (
            Path(dataset_path).parent / f"{Path(dataset_path).stem}_pii_report.txt"
        )

        with open(report_path, "w", encoding="utf-8") as f:
            f.write("PII Detection Report\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"Dataset: {dataset_path}\n")
            f.write(
                f"Analysis Date: {sys.version_info}\n\n"
            )  # Simple timestamp alternative

            f.write("Summary:\n")
            f.write(f"  Total columns analyzed: {len(all_columns)}\n")
            f.write(f"  Potential PII columns:  {len(unique_piis)}\n")
            f.write(
                f"  Clean columns:          {len(all_columns) - len(unique_piis)}\n\n"
            )

            if unique_piis:
                f.write("Detected PII Columns:\n")
                f.write("-" * 30 + "\n")
                for i, (column, methods) in enumerate(unique_piis.items(), 1):
                    methods_text = ", ".join(methods)
                    f.write(f"{i:2d}. {column:<25} → {methods_text}\n")

            f.write("\n" + "=" * 50 + "\n")
            f.write("Report generated by PII Detector CLI\n")

        print(f"✅ Report saved to: {report_path}")

    except Exception as e:
        print(f"❌ Error saving report: {e}")


if __name__ == "__main__":
    sys.exit(main())
