# PII Detector

A modern Python tool for identifying and handling personally identifiable information (PII) in datasets.

## About

This application identifies likely PII (personally identifiable information) in a dataset. To use:

- **End users**: Download the .exe installer from the [latest release](https://github.com/PovertyAction/PII_detection/releases/latest)
- **Developers**: Use the modern Python package with `uv` for development

This tool is currently in beta as it continues to be tested on IPA PII-containing field datasets.

## Quick Start

### For End Users

Download and run the latest installer from [GitHub Releases](https://github.com/PovertyAction/PII_detection/releases/latest).

### For Developers

```bash
# Clone the repository
git clone https://github.com/PovertyAction/PII_detection.git
cd PII_detection

# Set up development environment
just get-started

# Run the GUI application
just run-gui

# Or use the CLI
just run-cli --help

# For enhanced PII detection with Presidio (optional)
just install-presidio                    # Install with English small model
just install-presidio spanish md         # Install with Spanish medium model
uv run python examples/presidio_demo.py  # Test the installation

# For efficient batch processing of large datasets
just install-presidio-batch             # Install with batch processing support
just run-batch-demo                      # Run batch processing demonstration
```

## How it Works

The PII detector uses multiple detection strategies to identify potential PII in dataset columns:

### Core Detection Methods

1. **Column Name/Label Matching** - Matches column names against restricted word lists using strict or fuzzy matching
   - Check `find_piis_based_on_column_name()` in `src/pii_detector/core/processor.py`
   - Supports multiple languages (English, Spanish, Swahili)
   - Includes domain-specific terms (SurveyCTO, medical, locations)

2. **Format Pattern Detection** - Identifies phone numbers, dates, and other formatted data
   - Check `find_piis_based_on_column_format()` in `src/pii_detector/core/processor.py`
   - Expandable to GPS coordinates, national identifiers, etc.

3. **Sparsity Analysis** - Flags columns where most values are unique (open-ended questions)
   - Check `find_piis_based_on_sparse_entries()` in `src/pii_detector/core/processor.py`
   - Ideal for identifying free-text name/address fields

4. **Location Population Analysis** - Identifies small locations (< 20,000 people) that may be PII
   - Check `find_piis_based_on_locations_population()` in `src/pii_detector/core/processor.py`
   - Uses external APIs for population lookups

### Enhanced Detection with Presidio (Optional)

For improved accuracy, the tool integrates with Microsoft Presidio for ML-powered text analysis:

5. **Advanced Text Content Analysis** - Uses machine learning models to detect PII within text content
   - Check `src/pii_detector/core/presidio_engine.py` for Presidio integration
   - Context-aware detection using spaCy NLP models
   - Supports multiple languages with confidence scoring
   - Detects names, emails, phone numbers, SSNs, addresses, and more within free text

6. **Hybrid Detection** - Combines structural analysis with ML-based text analysis
   - Check `src/pii_detector/core/unified_processor.py` for unified detection
   - Confidence-weighted scoring from multiple detection methods
   - Graceful degradation when Presidio is not available

7. **Batch Processing** - Efficient processing for large datasets
   - Check `src/pii_detector/core/batch_processor.py` for batch processing capabilities
   - Chunked processing with parallel workers for improved performance
   - Memory-efficient handling of large datasets
   - Integration with presidio-structured for advanced tabular data processing

### User Workflow

1. Load your dataset (supports CSV, Excel, Stata formats)
2. Configure detection options (language, country, detection methods)
3. Review detected PII candidates
4. Choose actions for each column: **Drop**, **Encode**, or **Keep**
5. Export de-identified dataset, mapping files, and audit logs

## Batch Processing Examples

The tool includes efficient batch processing capabilities for large datasets. Here are practical examples using the included test data:

### Basic Batch Processing

```python
# Example 1: Analyze a single dataset with batch processing
import pandas as pd
from pii_detector.core.batch_processor import BatchPIIProcessor

# Initialize batch processor
processor = BatchPIIProcessor(
    chunk_size=1000,    # Process 1000 rows at a time
    max_workers=4       # Use 4 parallel workers
)

# Load test data
dataset = pd.read_csv("tests/data/comprehensive_pii_data.csv")

# Run batch detection
results = processor.detect_pii_batch(dataset)

# View results
for column, result in results.items():
    print(f"{column}: {result.detection_method} (confidence: {result.confidence:.2f})")
```

### Complete Batch Workflow

```python
# Example 2: Complete detection and anonymization workflow
from pii_detector.core.batch_processor import process_dataset_batch

# Process dataset with progress tracking
def show_progress(percent, message):
    print(f"Progress: {percent:.1f}% - {message}")

dataset = pd.read_csv("tests/data/sample_pii_data.csv")

# Run complete batch processing workflow
detection_results, anonymized_dataset, report = process_dataset_batch(
    dataset,
    language="en",
    chunk_size=500,
    max_workers=2,
    progress_callback=show_progress
)

print(f"Detected PII in {len(detection_results)} columns:")
for col, result in detection_results.items():
    print(f"  - {col}: {result.detection_method}")

print(f"\nAnonymization report:")
print(f"  - Original shape: {report['original_shape']}")
print(f"  - Final shape: {report['final_shape']}")
```

### DataFrame-Level Presidio Functions

```python
# Example 3: Use DataFrame-level Presidio functions for text analysis
from pii_detector.core.presidio_engine import (
    presidio_analyze_dataframe_batch,
    presidio_anonymize_dataframe_batch
)

# Load dataset with rich text content
dataset = pd.read_csv("tests/data/comprehensive_pii_data.csv")

# Analyze text columns for PII
analysis_results = presidio_analyze_dataframe_batch(
    dataset,
    text_columns=["full_name", "notes", "address"],
    confidence_threshold=0.7,
    sample_size=50
)

print("Presidio text analysis results:")
for col, result in analysis_results.items():
    entities = result.get('entities_found', {})
    print(f"  {col}: {list(entities.keys())} ({result.get('total_detections', 0)} detections)")

# Anonymize detected text columns
anonymized_df = presidio_anonymize_dataframe_batch(
    dataset,
    columns_to_anonymize=list(analysis_results.keys())
)

print("\nText anonymization complete!")
```

### Batch Processing Multiple Files

```python
# Example 4: Process multiple test files in batch
import glob
from pathlib import Path

# Process all CSV files in test data directory
csv_files = glob.glob("tests/data/*.csv")

for file_path in csv_files:
    print(f"\nProcessing: {Path(file_path).name}")

    try:
        dataset = pd.read_csv(file_path)

        # Quick batch analysis
        processor = BatchPIIProcessor(chunk_size=1000)
        results = processor.detect_pii_batch(dataset)

        print(f"  Dataset shape: {dataset.shape}")
        print(f"  PII columns found: {len(results)}")

        if results:
            print(f"  PII columns: {list(results.keys())}")

    except Exception as e:
        print(f"  Error: {e}")
```

### Performance Comparison

```python
# Example 5: Compare processing strategies
from pii_detector.core.batch_processor import BatchPIIProcessor

dataset = pd.read_csv("tests/data/comprehensive_pii_data.csv")

# Create multiple copies to simulate larger dataset
large_dataset = pd.concat([dataset] * 100, ignore_index=True)
print(f"Large dataset shape: {large_dataset.shape}")

processor = BatchPIIProcessor()

# Get processing strategy recommendation
strategy = processor.get_processing_strategy(large_dataset)
print(f"Recommended strategy: {strategy}")

# Get time estimates
estimates = processor.estimate_processing_time(large_dataset)
for strategy_name, estimate in estimates.items():
    print(f"{strategy_name}:")
    print(f"  Estimated time: {estimate['time_seconds']:.2f} seconds")
    print(f"  Memory usage: {estimate['memory_mb']:.1f} MB")
    print(f"  Recommended: {estimate['recommended']}")
```

### Test Data Files Description

The `tests/data/` directory contains sample datasets for testing:

- **`comprehensive_pii_data.csv`**: Rich dataset with multiple PII types (names, emails, SSNs, addresses, medical info, notes)
- **`sample_pii_data.csv`**: Basic PII dataset with standard identifiers
- **`clean_data.csv`**: Anonymized dataset with no PII (for testing clean data detection)
- **`qualitative_data.csv`**: Text-heavy data for testing Presidio text analysis
- **`test_data.csv`**: General test dataset

### Command Line Usage (Future)

```bash
# Once CLI is enhanced, these commands will work:

# Analyze single file
pii-detector analyze tests/data/sample_pii_data.csv --presidio --output-format json

# Batch process multiple files
pii-detector batch "tests/data/*.csv" --chunk-size 500 --workers 2

# Anonymize dataset
pii-detector anonymize tests/data/comprehensive_pii_data.csv --method presidio --output clean_data.csv
```

### Unstructured Text PII Detection

The tool includes functionality to identify PII within text content and replace it with placeholder strings (e.g., 'XXXXXX'). This allows preserving most text content while removing personal identifiers.

*Note: This feature is currently optimized for performance and may be disabled by default.*

## Project Structure

### Modern Python Package Layout

```text
src/pii_detector/
├── core/                    # Core PII detection algorithms
│   ├── processor.py         # Main data processing engine (legacy methods)
│   ├── text_analysis.py     # Basic text PII detection
│   ├── presidio_engine.py   # NEW: Microsoft Presidio ML-powered analysis
│   ├── unified_processor.py # NEW: Hybrid structural + ML detection
│   ├── hybrid_anonymizer.py # NEW: Advanced anonymization methods
│   ├── model_manager.py     # NEW: Dynamic spaCy model management
│   ├── hash_utils.py        # Basic hashing utilities
│   └── anonymization.py     # Comprehensive anonymization techniques
├── data/                    # Static data and configurations
│   ├── constants.py         # Application constants
│   ├── restricted_words.py  # Multi-language PII word lists
│   └── stopwords/           # Language-specific stopwords
├── gui/                     # Graphical user interface
│   └── frontend.py          # Modern tkinter application
├── cli/                     # Command-line interface
│   └── main.py              # CLI entry point
└── api/                     # External API integrations
    └── queries.py           # Location/population lookup services
```

### Supporting Files

- `assets/` - Application icons, logos, and PyInstaller hooks for spaCy/Presidio
- `examples/` - Demonstration scripts and usage examples
- `scripts/` - Utility scripts for model management and development
- `tests/` - Test suite with pytest
- `pyproject.toml` - Modern Python project configuration
- `Justfile` - Development workflow commands

## Development

### Requirements

- Python 3.9+
- [uv](https://docs.astral.sh/uv/) - Fast Python package manager
- [just](https://github.com/casey/just) - Command runner

### Development Commands

```bash
# Environment setup
just get-started           # Complete development setup
just venv                  # Create virtual environment
just install-deps         # Install dependencies

# Running the application
just run-gui              # Launch GUI interface
just run-gui-legacy       # Launch Legacy (0.23.0) GUI interface built in TKinter
just run-cli              # Launch CLI interface

# Enhanced PII detection (optional)
just install-presidio                    # Install Presidio with English small model
just install-presidio spanish md         # Install with Spanish medium model
just list-spacy-models                   # Show installed spaCy models
just manage-models list                  # Detailed model information
uv run python examples/presidio_demo.py  # Test Presidio functionality

# spaCy model management
just install-spacy-model en_core_web_md  # Install specific model
just manage-models ensure en lg          # Ensure English large model exists
just manage-models cleanup --keep en es  # Remove unused models

# Testing
just test                 # Run test suite (unit + integration)
uv run pytest tests/test_integration.py -v  # Run integration tests only
uv run pytest tests/test_presidio_integration.py -v  # Test Presidio integration
uv run pytest -m "slow"   # Run slow tests (includes API calls)
uv run pytest -m "not slow"  # Skip slow tests

# Code quality
just fmt-all              # Format and lint code
just pre-commit-run       # Run all pre-commit hooks

# Building and distribution
just build                # Build Python package
just build-exe            # Create Windows executable
just build-exe-presidio   # Create executable with Presidio support
just create-installer     # Generate Windows installer
```

### Test Data

The project includes comprehensive test datasets for integration testing:

- `tests/data/sample_pii_data.csv` - Dataset containing various PII types for testing detection algorithms
- `tests/data/clean_data.csv` - Clean dataset with minimal PII for testing false positive rates
- `tests/data/comprehensive_pii_data.csv` - Complex dataset with multiple PII types for anonymization testing
- `tests/data/qualitative_data.csv` - Text-based data for testing text anonymization techniques
- `tests/data/test_data.csv` - Simple dataset for basic functionality testing

These datasets are used by the integration test suite to verify that PII detection and anonymization work correctly across different scenarios.

### Anonymization Capabilities

The system provides extensive anonymization techniques based on academic research and FSD guidelines:

**Traditional Anonymization Methods:**

- Variable removal and record suppression
- Hash-based and systematic pseudonymization
- Age, income, and geographic categorization
- Statistical noise addition and permutation
- K-anonymity enforcement
- Text pattern masking and redaction

**Enhanced Anonymization with Presidio:**

- Context-aware text anonymization using ML models
- Entity-specific replacement strategies
- Confidence-based anonymization decisions
- Multi-language text processing

**Example Usage:**

*Traditional Methods:*

```python
from pii_detector.core.anonymization import AnonymizationTechniques

anonymizer = AnonymizationTechniques()

# Remove direct identifiers
clean_data = anonymizer.remove_variables(dataset, ['name', 'ssn', 'email'])

# Categorize sensitive data
clean_data['age_group'] = anonymizer.age_categorization(dataset['age'])
clean_data['income_bracket'] = anonymizer.income_categorization(dataset['income'])

# Apply k-anonymity
final_data = anonymizer.achieve_k_anonymity(clean_data, ['age_group', 'city'], k=3)
```

*Hybrid Anonymization with Presidio:*

```python
from pii_detector.core.unified_processor import detect_pii_unified
from pii_detector.core.hybrid_anonymizer import anonymize_dataset_hybrid

# Detect PII using hybrid methods
detection_results = detect_pii_unified(dataset, language="en")

# Anonymize using both traditional and ML-based methods
anonymized_data, report = anonymize_dataset_hybrid(dataset, detection_results)
```

See `examples/anonymization_demo.py` and `examples/presidio_demo.py` for complete demonstrations.

### spaCy Model Management

The enhanced PII detection uses spaCy language models. The system automatically manages model installation:

**Supported Languages:**

- English (`en`): en_core_web_sm, en_core_web_md, en_core_web_lg
- Spanish (`es`): es_core_news_sm, es_core_news_md, es_core_news_lg
- German (`de`): de_core_news_sm, de_core_news_md, de_core_news_lg
- French (`fr`): fr_core_news_sm, fr_core_news_md, fr_core_news_lg
- And more...

**Model Sizes:**

- `sm` (small): ~15MB, fast, good accuracy
- `md` (medium): ~50MB, balanced speed/accuracy
- `lg` (large): ~750MB, best accuracy, slower

**Management Commands:**

```bash
# Check what's installed
just list-spacy-models

# Install for specific language/size
just install-presidio german md

# Advanced model management
just manage-models list                    # Detailed model info
just manage-models ensure spanish lg       # Ensure model exists
just manage-models install en_core_web_lg  # Install specific model
just manage-models cleanup --keep en es    # Remove unused models
```

**Automatic Installation:**
The system automatically installs missing models when needed. No manual intervention required for basic usage.

### Environment Variables

For API integrations, set these optional environment variables:

- `GEONAMES_USERNAME` - GeoNames API for location population lookups
- `FOREBEARS_API_KEY` - Forebears API for name validation
- `PII_HASH_SECRET_KEY` - Secret key for hashing (uses default if not set)

## File Format Support

The PII Detector supports reading and writing multiple file formats:

- **CSV files** (`.csv`) - Universal comma-separated format
- **Excel files** (`.xlsx`, `.xls`) - Microsoft Excel formats
- **Stata files** (`.dta`) - Preserves variable labels and value labels, full round-trip support

### Command Line Format Handling

The CLI automatically detects input file formats and can preserve them in output:

```bash
# Anonymize Stata file, output as Stata
pii-detector anonymize survey_data.dta --output clean_survey.dta

# Batch process mixed formats, preserving original types
pii-detector batch "data/*" --output-dir results/
# → .dta files → .dta output, .csv files → .csv output, etc.

# Cross-format conversion supported
pii-detector anonymize data.dta --output data_clean.csv
```

## Distribution

### For End Users (Windows Executable)

```bash
# Create executable and installer
just build-exe
just create-installer

# Output locations:
# - Executable: dist/
# - Installer: compile create_installer.iss with Inno Setup
```

### For Python Package Distribution

```bash
# Build package for PyPI
just build

# Install locally in development mode
uv pip install -e .
```

## Contributing

1. Fork the repository
2. Set up development environment: `just get-started`
3. Make your changes
4. Run tests and formatting: `just fmt-all && just test`
5. Submit a pull request

## Credits

**Development Team:**

- IPA Global Research and Data Science Team

**Inspiration:**

- J-PAL: [stata_PII_scan](https://github.com/J-PAL/stata_PII_scan) (2020)
- J-PAL: [PII-Scan](https://github.com/J-PAL/PII-Scan) (2017)

## License

The PII Detector is [MIT Licensed](LICENSE).

---

**Feedback Welcome!** Help us improve this tool by reporting issues or suggestions on [GitHub Issues](https://github.com/PovertyAction/PII_detection/issues).
