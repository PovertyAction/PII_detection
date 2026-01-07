#!/usr/bin/env python3
"""Demonstration of comprehensive anonymization techniques.

This script shows how to use various anonymization methods
implemented based on FSD guidelines and academic research.
"""

import sys
from pathlib import Path

import pandas as pd

# Add the src directory to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from pii_detector.core.anonymization import AnonymizationTechniques


def main():
    """Demonstrate various anonymization techniques."""
    print("=== PII Anonymization Techniques Demo ===\n")

    # Create sample data
    sample_data = pd.DataFrame(
        {
            "participant_id": ["P001", "P002", "P003", "P004", "P005"],
            "name": [
                "John Doe",
                "Jane Smith",
                "Alice Johnson",
                "Bob Wilson",
                "Carol Davis",
            ],
            "email": [
                "john@email.com",
                "jane@company.org",
                "alice@uni.edu",
                "bob@tech.com",
                "carol@health.net",
            ],
            "age": [25, 34, 29, 45, 38],
            "income": [45000, 75000, 52000, 95000, 68000],
            "city": ["Chicago", "New York", "Chicago", "Los Angeles", "Chicago"],
            "occupation": ["Engineer", "Teacher", "Engineer", "Manager", "Nurse"],
            "phone": ["555-1234", "555-5678", "555-9012", "555-3456", "555-7890"],
            "notes": [
                "Called about billing on March 3rd",
                "Prefers email contact",
                "Works at Chicago Tech Corp",
                "Manager at LA Consulting",
                "Nurse at Memorial Hospital",
            ],
        }
    )

    print("Original Data:")
    print(sample_data)
    print("\n" + "=" * 80 + "\n")

    # Initialize anonymization techniques
    anonymizer = AnonymizationTechniques(random_seed=42)

    # 1. REMOVAL TECHNIQUES
    print("1. REMOVAL TECHNIQUES")
    print("-" * 20)

    # Remove direct identifiers
    step1 = anonymizer.remove_variables(sample_data, ["name", "email", "phone"])
    print("After removing direct identifiers (name, email, phone):")
    print(step1.head())
    print()

    # Remove records with unique combinations
    unique_removed = anonymizer.remove_records_with_unique_combinations(
        sample_data, ["city", "occupation"], threshold=1
    )
    print(
        f"Records with unique city-occupation combinations removed: {len(sample_data) - len(unique_removed)}"
    )
    print()

    # 2. PSEUDONYMIZATION TECHNIQUES
    print("2. PSEUDONYMIZATION TECHNIQUES")
    print("-" * 30)

    step2 = step1.copy()

    # Hash-based pseudonymization
    step2["participant_id"] = anonymizer.hash_pseudonymization(
        step1["participant_id"], prefix="ANON_"
    )
    print("Hash-based pseudonymization of participant IDs:")
    print(step2["participant_id"].head())
    print()

    # 3. RECODING/CATEGORIZATION
    print("3. RECODING/CATEGORIZATION TECHNIQUES")
    print("-" * 35)

    step3 = step2.copy()

    # Age categorization
    step3["age_group"] = anonymizer.age_categorization(step2["age"])
    print("Age categorization:")
    print(pd.DataFrame({"original_age": step2["age"], "age_group": step3["age_group"]}))
    print()

    # Income categorization
    step3["income_bracket"] = anonymizer.income_categorization(step2["income"])
    print("Income categorization:")
    print(
        pd.DataFrame(
            {
                "original_income": step2["income"],
                "income_bracket": step3["income_bracket"],
            }
        )
    )
    print()

    # Top/bottom coding
    step3["income_coded"] = anonymizer.top_bottom_coding(
        step2["income"], top_percentile=80, bottom_percentile=20
    )
    print("Top/bottom coding of income (80th/20th percentiles):")
    print(pd.DataFrame({"original": step2["income"], "coded": step3["income_coded"]}))
    print()

    # 4. RANDOMIZATION TECHNIQUES
    print("4. RANDOMIZATION TECHNIQUES")
    print("-" * 25)

    step4 = step3.copy()

    # Add noise to numeric data
    step4["age_with_noise"] = anonymizer.add_noise(
        step3["age"], noise_type="gaussian", noise_level=0.1
    )
    print("Gaussian noise added to age:")
    print(
        pd.DataFrame({"original": step3["age"], "with_noise": step4["age_with_noise"]})
    )
    print()

    # Permutation swapping
    swapped_data = anonymizer.permutation_swapping(
        step4, ["age", "income"], swap_probability=0.4
    )
    print("After permutation swapping (age and income):")
    print(
        pd.DataFrame(
            {
                "original_age": step4["age"],
                "swapped_age": swapped_data["age"],
                "original_income": step4["income"],
                "swapped_income": swapped_data["income"],
            }
        )
    )
    print()

    # 5. TEXT ANONYMIZATION
    print("5. TEXT ANONYMIZATION")
    print("-" * 20)

    # Text masking
    sample_text = "John Doe called from 555-1234 about his account john@email.com"
    masked_text = anonymizer.text_masking(sample_text)
    print(f"Original text: {sample_text}")
    print(f"Masked text:   {masked_text}")
    print()

    # Apply to notes column
    masked_notes = sample_data["notes"].apply(anonymizer.text_masking)
    print("Original vs Masked notes:")
    for i, (orig, masked) in enumerate(zip(sample_data["notes"], masked_notes)):
        print(f"  {i + 1}. {orig}")
        print(f"     → {masked}")
    print()

    # 6. K-ANONYMITY
    print("6. K-ANONYMITY ANALYSIS")
    print("-" * 20)

    # Check k-anonymity
    test_data = pd.DataFrame(
        {
            "age_group": ["20-30", "20-30", "30-40", "30-40", "40-50"],
            "city": ["Chicago", "Chicago", "NYC", "NYC", "LA"],
            "occupation": ["Engineer", "Teacher", "Engineer", "Teacher", "Manager"],
            "salary": [50000, 45000, 75000, 65000, 95000],
        }
    )

    is_anonymous, violations = anonymizer.k_anonymity_check(
        test_data, ["age_group", "city"], k=2
    )
    print(f"Original data satisfies 2-anonymity: {is_anonymous}")
    if not is_anonymous:
        print("Violations:")
        print(violations)

    # Achieve k-anonymity
    k_anonymous_data = anonymizer.achieve_k_anonymity(
        test_data, ["age_group", "city"], k=2
    )
    is_now_anonymous, _ = anonymizer.k_anonymity_check(
        k_anonymous_data, ["age_group", "city"], k=2
    )
    print(f"After applying k-anonymity: {is_now_anonymous}")
    print(f"Rows removed: {len(test_data) - len(k_anonymous_data)}")
    print()

    # 7. COMPREHENSIVE WORKFLOW
    print("7. COMPREHENSIVE ANONYMIZATION WORKFLOW")
    print("-" * 40)

    # Apply full workflow
    final_data = sample_data.copy()

    # Step 1: Remove direct identifiers
    final_data = anonymizer.remove_variables(final_data, ["name", "email", "phone"])

    # Step 2: Pseudonymize IDs
    final_data["participant_id"] = anonymizer.hash_pseudonymization(
        final_data["participant_id"], prefix="SUBJ_"
    )

    # Step 3: Categorize continuous variables
    final_data["age_group"] = anonymizer.age_categorization(final_data["age"])
    final_data["income_bracket"] = anonymizer.income_categorization(
        final_data["income"]
    )
    final_data = final_data.drop(["age", "income"], axis=1)

    # Step 4: Anonymize text
    final_data["notes"] = final_data["notes"].apply(anonymizer.text_masking)

    # Step 5: Apply k-anonymity
    final_data = anonymizer.achieve_k_anonymity(
        final_data, ["age_group", "city", "occupation"], k=2
    )

    print("Final anonymized dataset:")
    print(final_data)
    print()

    # 8. ANONYMIZATION REPORT
    print("8. ANONYMIZATION REPORT")
    print("-" * 20)

    report = anonymizer.anonymization_report(sample_data, final_data)
    print(f"Original rows: {report['original_rows']}")
    print(f"Anonymized rows: {report['anonymized_rows']}")
    print(
        f"Rows removed: {report['rows_removed']} ({report['removal_percentage']:.1f}%)"
    )
    print("\nColumn transformations:")
    for col, stats in report["columns_comparison"].items():
        if col in final_data.columns:
            print(
                f"  {col}: {stats['original_unique_values']} → {stats['anonymized_unique_values']} unique values "
                f"({stats['uniqueness_reduction']:.1f}% reduction)"
            )


if __name__ == "__main__":
    main()
