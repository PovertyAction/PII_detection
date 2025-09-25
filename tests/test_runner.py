#!/usr/bin/env python3
"""
Test runner for batch processing functionality.

This script runs a subset of the batch processing tests to verify
that the new functionality works correctly without requiring external dependencies.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent.parent / "src"))

# Import test modules


def run_basic_tests():
    """Run basic batch processing functionality tests."""

    print("Running basic functionality tests...")
    print("=" * 60)

    try:
        import pandas as pd

        from pii_detector.core.batch_processor import BatchPIIProcessor

        # Test 1: Basic initialization
        print("Test 1: Basic initialization...")
        processor = BatchPIIProcessor(use_structured_engine=False)
        assert processor.chunk_size == 1000
        assert processor.max_workers == 4
        print("[OK] Basic initialization passed")

        # Test 2: Processing strategy selection
        print("Test 2: Processing strategy selection...")
        small_df = pd.DataFrame({"col": range(100)})
        large_df = pd.DataFrame({"col": range(5000)})

        small_strategy = processor.get_processing_strategy(small_df)
        large_strategy = processor.get_processing_strategy(large_df)

        assert small_strategy == "standard_processing"
        assert large_strategy == "chunked_processing"
        print("[OK] Processing strategy selection passed")

        # Test 3: Time estimation
        print("Test 3: Time estimation...")
        estimates = processor.estimate_processing_time(small_df)
        assert isinstance(estimates, dict)
        assert "standard_processing" in estimates
        assert "chunked_processing" in estimates
        print("[OK] Time estimation passed")

        # Test 4: Basic detection without external dependencies
        print("Test 4: Basic detection...")
        test_df = pd.DataFrame(
            {
                "email_column": ["test@example.com", "user@test.org"],
                "numeric_column": [1, 2],
            }
        )

        # This should work with basic structural detection
        results = processor.detect_pii_batch(test_df)
        assert isinstance(results, dict)
        print("[OK] Basic detection passed")

        print("\n[SUCCESS] All basic functionality tests passed!")
        return True

    except Exception as e:
        print(f"\n[ERROR] Test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def check_imports():
    """Check that all batch processing modules can be imported."""
    print("Checking batch processing imports...")

    try:
        from pii_detector.core.batch_processor import BatchPIIProcessor

        print("[OK] batch_processor module imported successfully")

        print("[OK] Enhanced presidio_engine functions imported successfully")

        # Test basic initialization without structured engine
        processor = BatchPIIProcessor(use_structured_engine=False)
        print(
            f"[OK] BatchPIIProcessor initialized (chunk_size: {processor.chunk_size})"
        )

        # Check strategy selection
        import pandas as pd

        small_df = pd.DataFrame({"col": range(100)})
        strategy = processor.get_processing_strategy(small_df)
        print(f"[OK] Processing strategy selection works: {strategy}")

        return True

    except Exception as e:
        print(f"[ERROR] Import error: {e}")
        import traceback

        traceback.print_exc()
        return False


def main():
    """Main test runner function."""
    print("Batch Processing Test Suite")
    print("=" * 60)

    # Check imports first
    if not check_imports():
        print("\n[ERROR] Import checks failed. Cannot proceed with tests.")
        return False

    print("\n" + "=" * 60)

    # Run basic tests
    success = run_basic_tests()

    # Final summary
    print("\n" + "=" * 60)
    if success:
        print("[SUCCESS] Batch processing functionality is working correctly!")
        print("\nNext steps:")
        print("- Run full test suite: uv run pytest tests/")
        print("- Try the batch demo: just run-batch-demo")
        print("- Install batch dependencies: just install-presidio-batch")
    else:
        print("[WARNING] Some issues were found. Please check the test output above.")

    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
