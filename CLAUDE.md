# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

This is a modern Python-based PII (Personally Identifiable Information) detection tool that identifies potential PII in datasets and helps create de-identified versions. The application provides both a GUI interface and CLI for analyzing CSV, Excel, and Stata files. Built with modern Python packaging using uv and pyproject.toml.

## Commands

### Environment Setup

```bash
# Get started with development environment
just get-started

# Or manually:
uv venv
uv sync
```

### Running the Application

```bash
# Launch GUI
just run-gui
# or
uv run python -m pii_detector.gui.frontend

# Launch CLI
just run-cli
# or
uv run python -m pii_detector.cli.main --help

# Install Presidio for enhanced PII detection (default: English, small model)
just install-presidio

# Install Presidio with specific language and model size
just install-presidio spanish md  # Spanish, medium model
just install-presidio german lg   # German, large model

# Install specific spaCy model
just install-spacy-model en_core_web_md

# List available spaCy models
just list-spacy-models

# Run Presidio demonstration
uv run python examples/presidio_demo.py
```

### Development Workflow

```bash
# Install dependencies
uv sync

# Run tests
just test

# Code formatting and linting
just fmt-all

# Build package
just build
```

### Legacy Executable Creation

```bash
# Create Windows executable (maintains backward compatibility)
just build-exe

# Create Windows executable with Presidio support
just build-exe-presidio

# Create installer
just create-installer
```

## Architecture

### Modern Package Structure

```text
src/pii_detector/
├── __init__.py              # Package initialization
├── core/                    # Core PII detection logic
│   ├── processor.py         # Main data processing engine (legacy methods)
│   ├── text_analysis.py     # Basic text PII detection
│   ├── presidio_engine.py   # NEW: Presidio ML-powered text analysis
│   ├── unified_processor.py # NEW: Hybrid structural + ML detection
│   ├── hybrid_anonymizer.py # NEW: Combined anonymization methods
│   ├── hash_utils.py        # Basic hashing utilities
│   └── anonymization.py     # Comprehensive anonymization techniques
├── data/                    # Static data and configurations
│   ├── constants.py         # Application constants
│   ├── restricted_words.py  # Multi-language PII word lists
│   └── stopwords/           # Language-specific stopwords
├── gui/                     # Graphical user interface
│   └── frontend.py          # Modern tkinter GUI application
├── cli/                     # Command-line interface
│   └── main.py              # CLI entry point
└── api/                     # External API integrations
    └── queries.py           # Location/population lookup services
```

### Core Components

**GUI Layer:**

- `src/pii_detector/gui/frontend.py` - Modern tkinter GUI with improved error handling, class-based design, and better UX

**CLI Layer:**

- `src/pii_detector/cli/main.py` - Command-line interface supporting both GUI launch and direct file processing

**Data Processing Layer:**

- `src/pii_detector/core/processor.py` - Core backend engine with type hints, improved error handling, and modern Python patterns
- `src/pii_detector/core/text_analysis.py` - Basic text-based PII detection with regex patterns
- `src/pii_detector/core/presidio_engine.py` - **NEW**: Microsoft Presidio integration for ML-powered text analysis
- `src/pii_detector/core/unified_processor.py` - **NEW**: Hybrid detection combining structural analysis with Presidio
- `src/pii_detector/core/hybrid_anonymizer.py` - **NEW**: Advanced anonymization using both statistical and ML methods

**Configuration and Data:**

- `src/pii_detector/data/constants.py` - Type-safe constants with clear organization
- `src/pii_detector/data/restricted_words.py` - Centralized word lists with proper typing and documentation
- `src/pii_detector/data/stopwords/` - Language-specific stopword files for text processing

**External Integration:**

- `src/pii_detector/api/queries.py` - Location population queries with improved error handling and API credential management

**Utilities:**

- `src/pii_detector/core/hash_utils.py` - Basic hashing utilities for pseudonymization
- `src/pii_detector/core/anonymization.py` - Comprehensive anonymization techniques based on academic research

### PII Detection Methods

The system uses four primary detection strategies implemented in `src/pii_detector/core/processor.py`:

1. **Column Name/Label Matching** (`find_piis_based_on_column_name()`) - Matches column names against restricted word lists using strict or fuzzy matching
2. **Format Pattern Detection** (`find_piis_based_on_column_format()`) - Identifies phone numbers, dates, and other formatted data
3. **Sparsity Analysis** (`find_piis_based_on_sparse_entries()`) - Flags columns where most values are unique (open-ended questions)
4. **Location Population Checks** (`find_piis_based_on_locations_population()`) - Identifies small locations via external API queries

### Comprehensive Anonymization Techniques

The system provides extensive anonymization capabilities in `src/pii_detector/core/anonymization.py` based on FSD guidelines and academic research:

**Removal Techniques:**
- **Variable Removal** - Complete deletion of identifying columns
- **Record Removal** - Elimination of records with unique quasi-identifier combinations
- **Selective Suppression** - Targeted removal of specific data points

**Pseudonymization Methods:**
- **Hash-based Pseudonymization** - Consistent pseudonyms using cryptographic hashing
- **Name Replacement** - Systematic replacement with generic identifiers
- **Identifier Encoding** - Convert identifiers to non-reversible codes

**Recoding/Categorization:**
- **Age Categorization** - Convert ages to broad age groups
- **Income Bracketing** - Group income values into ranges
- **Geographic Generalization** - Convert specific locations to broader regions
- **Date Generalization** - Reduce date precision (year, month, quarter)
- **Top/Bottom Coding** - Cap extreme values in continuous variables

**Randomization Techniques:**
- **Noise Addition** - Add statistical noise (Gaussian or uniform) to numeric data
- **Permutation Swapping** - Randomly swap values between records
- **Data Perturbation** - Introduce controlled random variations

**Statistical Disclosure Control:**
- **K-anonymity** - Ensure each record is indistinguishable from k-1 others
- **L-diversity** - Maintain diversity in sensitive attributes (mock implementation)
- **T-closeness** - Preserve overall distribution of sensitive attributes (mock)
- **Differential Privacy** - Add calibrated noise for privacy guarantees (mock)

**Text Anonymization:**
- **Pattern Masking** - Replace PII patterns (emails, phones, SSNs) with placeholders
- **Selective Text Suppression** - Remove specific types of information from text
- **Named Entity Redaction** - Identify and mask person/location names in text

**Quality Assurance:**
- **Anonymization Reporting** - Detailed reports on transformations applied
- **Data Utility Metrics** - Measure information loss from anonymization
- **Privacy Risk Assessment** - Evaluate remaining disclosure risks

### Data Flow

1. User selects dataset file through GUI (`app_frontend.py`)
2. File is loaded and parsed (`import_dataset()` in `PII_data_processor.py`)
3. PII detection algorithms are applied based on user-selected options
4. Results are presented in GUI for user review and action selection (Drop/Encode/Keep)
5. De-identified dataset and accompanying files are generated based on user choices

### File Format Support

- **CSV/Excel**: Direct pandas import
- **Stata (.dta)**: Preserves variable labels and value labels for comprehensive analysis

### Key Dependencies

- `pandas` - Primary data manipulation
- `tkinter` - GUI framework
- `requests` - API communication for location lookups
- `selenium` - Web scraping capabilities (likely for location data)
- PyInstaller ecosystem for executable creation

## Development Notes

### Modern Python Practices

- **Type hints**: Core modules use type annotations for better code documentation and IDE support
- **Error handling**: Improved exception handling and user feedback throughout the application
- **Code organization**: Clear separation of concerns with dedicated modules for each functionality
- **Environment variables**: Secure handling of API keys and configuration through environment variables

### Build System

- **uv build backend**: Fast, modern build system replacing setuptools
- **pyproject.toml**: Centralized project configuration following PEP 518 standards
- **just task runner**: Simplified development workflow with cross-platform commands
- **pre-commit hooks**: Automated code quality checks with ruff formatting and linting

### Testing and Quality

- **pytest framework**: Modern testing setup with coverage reporting
- **ruff**: Fast Python linter and formatter replacing multiple tools
- **codespell**: Spell checking for documentation and code comments
- **CI/CD ready**: Configuration files support automated testing workflows

### Backward Compatibility

- **Executable creation**: Maintains PyInstaller workflow for Windows deployment
- **Asset handling**: Logo and template files preserved in `assets/` directory
- **Functionality preservation**: All original PII detection capabilities maintained

### Deployment Options

- **Package installation**: `uv pip install .` for local development
- **Executable distribution**: Traditional `.exe` creation for end users
- **PyPI ready**: Package structure supports publishing to Python Package Index
- **Cross-platform**: Works on Windows, macOS, and Linux (GUI requires display)

### API Integration

- **GeoNames API**: Location population lookup (requires `GEONAMES_USERNAME` environment variable)
- **Forebears API**: Name validation service (requires `FOREBEARS_API_KEY` environment variable)
- **Chrome/Selenium**: Google search fallback for population data (requires ChromeDriver)
