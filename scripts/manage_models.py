#!/usr/bin/env python3
"""Utility script for managing spaCy models for PII detection.

This script provides a command-line interface for installing, listing, and managing
spaCy models used by Presidio for enhanced PII detection.
"""

import argparse
import sys

try:
    from pii_detector.core.model_manager import get_model_manager

    MANAGER_AVAILABLE = True
except ImportError as e:
    print(f"Error: Could not import model manager: {e}")
    print("Please install the presidio dependencies first: just install-presidio")
    MANAGER_AVAILABLE = False


def list_models():
    """List installed and available spaCy models."""
    if not MANAGER_AVAILABLE:
        return False

    manager = get_model_manager()

    print("=== spaCy Model Status ===")
    print(f"spaCy Available: {manager.spacy_available}")

    if manager.spacy_available:
        print(f"Installed Models: {manager.installed_models}")
        print(f"Available Languages: {manager.get_available_languages()}")

        # Show details for installed models
        if manager.installed_models:
            print("\n=== Installed Model Details ===")
            for model in manager.installed_models:
                info = manager.get_model_info(model)
                if info["status"] == "available":
                    print(f"  {model}:")
                    print(f"    Language: {info['language']}")
                    print(f"    Size: {info['size']}")
                    print(f"    Version: {info['version']}")
                    print(f"    Components: {', '.join(info['components'])}")
                else:
                    print(f"  {model}: {info['status']}")

    return True


def install_model(model_name: str, force: bool = False):
    """Install a specific spaCy model."""
    if not MANAGER_AVAILABLE:
        return False

    manager = get_model_manager()

    print(f"Installing spaCy model: {model_name}")
    if force:
        print("(Force installation enabled)")

    success = manager.install_model(model_name, force=force)

    if success:
        print(f"✓ Successfully installed {model_name}")

        # Show model info
        info = manager.get_model_info(model_name)
        if info["status"] == "available":
            print(f"  Language: {info['language']}")
            print(f"  Size: {info['size']}")
            print(f"  Version: {info['version']}")
    else:
        print(f"✗ Failed to install {model_name}")

    return success


def install_language_model(language: str, size: str = "sm"):
    """Install the best model for a language."""
    if not MANAGER_AVAILABLE:
        return False

    manager = get_model_manager()

    print(f"Installing {size} model for {language}...")
    model_name = manager.install_default_model(language, size)

    if model_name:
        print(f"✓ Successfully installed {model_name}")

        # Show model info
        info = manager.get_model_info(model_name)
        if info["status"] == "available":
            print(f"  Language: {info['language']}")
            print(f"  Size: {info['size']}")
            print(f"  Version: {info['version']}")
    else:
        print(f"✗ Failed to install model for {language}")

    return model_name is not None


def ensure_model(language: str, size: str = "sm"):
    """Ensure a model is available for a language."""
    if not MANAGER_AVAILABLE:
        return False

    manager = get_model_manager()

    print(f"Ensuring {size} model for {language} is available...")
    model_name = manager.ensure_model_available(language, size)

    if model_name:
        print(f"✓ Model available: {model_name}")
        return True
    else:
        print(f"✗ Could not ensure model availability for {language}")
        return False


def cleanup_models(keep_languages: list[str] | None = None):
    """Remove unused spaCy models."""
    if not MANAGER_AVAILABLE:
        return False

    manager = get_model_manager()

    if keep_languages:
        print(f"Cleaning up models, keeping languages: {keep_languages}")
    else:
        print("Cleaning up all unused models...")

    manager.cleanup_unused_models(keep_languages)
    print("✓ Cleanup complete")

    return True


def main():
    """Run main entry point."""
    if not MANAGER_AVAILABLE:
        sys.exit(1)

    parser = argparse.ArgumentParser(
        description="Manage spaCy models for PII detection",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s list                          # List all models
  %(prog)s install en_core_web_sm        # Install specific model
  %(prog)s install-lang en md            # Install medium English model
  %(prog)s ensure en sm                  # Ensure small English model exists
  %(prog)s cleanup --keep en es          # Remove models except English/Spanish
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # List command
    subparsers.add_parser("list", help="List installed and available models")

    # Install specific model
    install_parser = subparsers.add_parser(
        "install", help="Install specific spaCy model"
    )
    install_parser.add_argument("model_name", help="Name of the model to install")
    install_parser.add_argument(
        "--force", action="store_true", help="Force installation"
    )

    # Install language model
    lang_parser = subparsers.add_parser(
        "install-lang", help="Install model for language"
    )
    lang_parser.add_argument("language", help="Language code (en, es, de, etc.)")
    lang_parser.add_argument(
        "size", nargs="?", default="sm", choices=["sm", "md", "lg"], help="Model size"
    )

    # Ensure model
    ensure_parser = subparsers.add_parser("ensure", help="Ensure model is available")
    ensure_parser.add_argument("language", help="Language code")
    ensure_parser.add_argument(
        "size", nargs="?", default="sm", choices=["sm", "md", "lg"], help="Model size"
    )

    # Cleanup
    cleanup_parser = subparsers.add_parser("cleanup", help="Remove unused models")
    cleanup_parser.add_argument(
        "--keep", nargs="*", metavar="LANG", help="Languages to keep models for"
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    try:
        if args.command == "list":
            success = list_models()
        elif args.command == "install":
            success = install_model(args.model_name, args.force)
        elif args.command == "install-lang":
            success = install_language_model(args.language, args.size)
        elif args.command == "ensure":
            success = ensure_model(args.language, args.size)
        elif args.command == "cleanup":
            success = cleanup_models(args.keep)
        else:
            parser.print_help()
            success = False

        if not success:
            sys.exit(1)

    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
