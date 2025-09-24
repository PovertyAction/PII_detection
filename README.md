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
```

## How it Works

The PII detector uses multiple detection strategies to identify potential PII in dataset columns:

### Detection Methods

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

### User Workflow

1. Load your dataset (supports CSV, Excel, Stata formats)
2. Configure detection options (language, country, detection methods)
3. Review detected PII candidates
4. Choose actions for each column: **Drop**, **Encode**, or **Keep**
5. Export de-identified dataset, mapping files, and audit logs

### Unstructured Text PII Detection

The tool includes functionality to identify PII within text content and replace it with placeholder strings (e.g., 'XXXXXX'). This allows preserving most text content while removing personal identifiers.

*Note: This feature is currently optimized for performance and may be disabled by default.*

## Project Structure

### Modern Python Package Layout

```
src/pii_detector/
├── core/                    # Core PII detection algorithms
│   ├── processor.py         # Main data processing engine
│   ├── text_analysis.py     # Unstructured text PII detection
│   └── hash_utils.py        # Anonymization utilities
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

- `assets/` - Application icons, logos, and templates
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
just run-cli              # Launch CLI interface

# Testing
just test                 # Run test suite (unit + integration)
uv run pytest tests/test_integration.py -v  # Run integration tests only
uv run pytest -m "slow"   # Run slow tests (includes API calls)
uv run pytest -m "not slow"  # Skip slow tests

# Code quality
just fmt-all              # Format and lint code
just pre-commit-run       # Run all pre-commit hooks

# Building and distribution
just build                # Build Python package
just build-exe            # Create Windows executable
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

**Data Anonymization Methods:**
- Variable removal and record suppression
- Hash-based and systematic pseudonymization
- Age, income, and geographic categorization
- Statistical noise addition and permutation
- K-anonymity enforcement
- Text pattern masking and redaction

**Example Usage:**
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

See `examples/anonymization_demo.py` for a complete demonstration.

### Environment Variables

For API integrations, set these optional environment variables:

- `GEONAMES_USERNAME` - GeoNames API for location population lookups
- `FOREBEARS_API_KEY` - Forebears API for name validation
- `PII_HASH_SECRET_KEY` - Secret key for hashing (uses default if not set)

## File Format Support

- **CSV files** (`.csv`)
- **Excel files** (`.xlsx`, `.xls`)
- **Stata files** (`.dta`) - Preserves variable labels and value labels

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
