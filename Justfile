# PII Detector Development Workflow
# Requires: just, uv

set windows-shell := ["powershell.exe", "-NoLogo", "-Command"]

# Set path to virtual environment's python

python_dir := ".venv/"
python := python_dir + if os_family() == "windows" { "Script/python.exe" } else { "/python3" }

# List available commands
default:
    @just --list

# Display system information
system-info:
    @echo "CPU architecture: {{ arch() }}"
    @echo "Operating system type: {{ os_family() }}"
    @echo "Operating system: {{ os() }}"

# Initial set up and global installations
get-started: pre-install venv activate-venv

# Environment setup and management
clean:
    @echo "Removing virtual environment..."
    uv venv --rm || true
    @echo "Environment cleaned."

# create virtual environment
venv:
    uv sync
    uv tool install pre-commit
    pre-commit install

activate-venv:
    @echo "To activate the virtual environment, run:"
    @echo "  .venv\\Scripts\\activate  (Windows)"
    @echo "  source .venv/bin/activate  (Unix)"

update-reqs:
    @echo "Updating dependencies and pre-commit hooks..."
    uv sync --upgrade
    uv run pre-commit autoupdate

# Application execution
run-gui:
    @echo "Launching PII Detector GUI..."
    uv run python -m pii_detector.gui.frontend

run-cli:
    @echo "Launching PII Detector CLI..."
    uv run python -m pii_detector.cli.main

# Development tools
test:
    @echo "Running test suite..."
    uv run pytest

test-cov:
    @echo "Running tests with coverage report..."
    uv run pytest --cov-report=html
    @echo "Coverage report generated in htmlcov/"

# Code quality
lint-py:
    @echo "Linting Python code..."
    uv run ruff check src/ tests/

fmt-python:
    @echo "Formatting Python code..."
    uv run ruff format src/ tests/

lint-fix:
    @echo "Linting and fixing Python code..."
    uv run ruff check --fix src/ tests/

spell-check:
    @echo "Checking spelling..."
    uv run codespell src/ tests/ docs/ README.md

# Format all markdown and config files
fmt-markdown:
    markdownlint --config .markdownlint.yaml "**/*.{md,qmd}" --fix

# Format a single markdown file, "f"
fmt-md f:
    markdownlint --config .markdownlint.yaml {{ f }} --fix

# Check format of all markdown files
fmt-check-markdown:
    markdownlint --config .markdownlint.yaml "**/*.{md,qmd}"

fmt-all: fmt-python lint-fix spell-check fmt-markdown
    @echo "All formatting and linting complete!"

# Pre-commit hooks
pre-commit-install:
    @echo "Installing pre-commit hooks..."
    uv run pre-commit install

pre-commit-run:
    @echo "Running pre-commit hooks..."
    uv run pre-commit run --all-files

# Build and distribution
build:
    @echo "Building distribution packages..."
    uv build

install-local:
    @echo "Installing package locally in development mode..."
    uv pip install -e .

# Executable creation
build-exe:
    @echo "Creating Windows executable with PyInstaller..."
    uv run pyinstaller --windowed --name=pii_detector --icon=assets/app-icon.ico --add-data="assets/app-icon.ico;." --add-data="assets/ipa-logo.jpg;." --add-data="assets/anonymize_script_template_v2.do;." --additional-hooks-dir=assets --hiddenimport srsly.msgpack.util --noconfirm src/pii_detector/gui/frontend.py

# Documentation
docs-serve:
    @echo "Serving documentation locally..."
    @echo "Documentation serving not yet implemented"

# Cleanup
clean-build:
    @echo "Cleaning build artifacts..."
    rm -rf dist/ build/ *.egg-info/ htmlcov/ .coverage .pytest_cache/

clean-all: clean clean-build
    @echo "All clean!"

# Platform-specific pre-install commands
[windows]
pre-install:
    @echo "Installing Windows prerequisites..."
    @echo "Ensure you have installed: just, uv"
    winget install Git.Git Casey.Just astral-sh.uv OpenJS.NodeJS
    npm install -g markdownlint-cli

[linux]
pre-install:
    @echo "Installing Unix prerequisites..."
    @echo "Ensure you have Homebrew installed: https://brew.sh/"
    brew install just uv markdownlint-cli

[macos]
pre-install:
    @echo "Installing macOS prerequisites..."
    @echo "Ensure you have Homebrew installed: https://brew.sh/"
    brew install just uv markdownlint-cli
