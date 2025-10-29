"""Main entry point for the Flet-based PII Detector application."""

import sys
from pathlib import Path

import flet as ft

# Add src to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

from pii_detector.gui.flet_app.ui.app import PIIDetectorApp
from pii_detector.gui.flet_app.ui.themes.ipa_theme import create_ipa_theme


def main(page: ft.Page):
    """Main application entry point."""  # noqa: D401
    # Configure desktop app
    page.title = "IPA PII Detector"
    page.window_width = 1200
    page.window_height = 800
    page.window_min_width = 800
    page.window_min_height = 600
    page.theme_mode = ft.ThemeMode.LIGHT
    page.theme = create_ipa_theme()
    page.padding = 0
    page.spacing = 0

    # Initialize and run the app
    app = PIIDetectorApp(page)
    app.initialize()


if __name__ == "__main__":
    # For development
    ft.app(target=main)
