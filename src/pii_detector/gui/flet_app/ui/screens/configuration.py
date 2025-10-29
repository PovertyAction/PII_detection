"""Configuration screen for PII detection settings."""

import flet as ft

from pii_detector.gui.flet_app.config.constants import (
    AppConstants,
    IPAColors,
    IPASpacing,
    IPATypography,
)
from pii_detector.gui.flet_app.config.settings import AppState, DetectionConfig
from pii_detector.gui.flet_app.ui.components.buttons import (
    create_primary_button,
    create_secondary_button,
)


class ConfigurationScreen:
    """Configuration screen implementation."""

    def __init__(self, page: ft.Page, state_manager):
        """Initialize the configuration screen.

        Args:
            page: Flet page instance
            state_manager: Application state manager

        """
        self.page = page
        self.state_manager = state_manager
        self._screen_name = AppConstants.SCREEN_CONFIGURATION

        # Preset buttons for detection configuration
        self.preset_quick = ft.ElevatedButton(
            text="Quick",
            style=ft.ButtonStyle(
                bgcolor=IPAColors.LIGHT_GREY, color=IPAColors.CHARCOAL
            ),
            on_click=lambda e: self._set_preset("quick"),
        )
        self.preset_balanced = ft.ElevatedButton(
            text="Balanced",
            style=ft.ButtonStyle(bgcolor=IPAColors.IPA_GREEN, color=IPAColors.WHITE),
            on_click=lambda e: self._set_preset("balanced"),
        )
        self.preset_thorough = ft.ElevatedButton(
            text="Thorough",
            style=ft.ButtonStyle(
                bgcolor=IPAColors.LIGHT_GREY, color=IPAColors.CHARCOAL
            ),
            on_click=lambda e: self._set_preset("thorough"),
        )

        # Detection method expandable sections
        self.column_name_expanded = False
        self.format_pattern_expanded = False
        self.sparsity_expanded = False
        self.location_expanded = False
        self.presidio_expanded = False

        # Detection method checkboxes (now part of expandable sections)
        self.column_name_check = ft.Checkbox(value=True)
        self.format_pattern_check = ft.Checkbox(value=True)
        self.sparsity_check = ft.Checkbox(value=True)
        self.location_check = ft.Checkbox(value=False)
        self.presidio_check = ft.Checkbox(value=False)

    def build(self) -> ft.Container:
        """Build the configuration screen."""
        # Create the detection methods container
        self.detection_methods_container = ft.Column(spacing=IPASpacing.SM)
        self._build_all_detection_methods()

        return ft.Container(
            content=ft.Column(
                [
                    # Title
                    ft.Text(
                        "Detection Configuration",
                        size=IPATypography.HEADER_2,
                        weight=ft.FontWeight.W_600,
                        color=IPAColors.DARK_BLUE,
                    ),
                    ft.Text(
                        "Configure PII detection methods for your analysis. You'll select anonymization methods for each detected column on the Results screen.",
                        size=IPATypography.BODY_REGULAR,
                        color=IPAColors.CHARCOAL,
                    ),
                    # Detection Methods Section
                    ft.Container(
                        content=ft.Column(
                            [
                                ft.Text(
                                    "Detection Configuration",
                                    size=IPATypography.HEADER_3,
                                    weight=ft.FontWeight.W_500,
                                    color=IPAColors.CHARCOAL,
                                ),
                                # Preset buttons
                                ft.Row(
                                    [
                                        self.preset_quick,
                                        self.preset_balanced,
                                        self.preset_thorough,
                                    ],
                                    alignment=ft.MainAxisAlignment.CENTER,
                                    spacing=IPASpacing.SM,
                                ),
                                # Expandable detection method sections
                                self.detection_methods_container,
                            ],
                            spacing=IPASpacing.SM,
                        ),
                        padding=IPASpacing.MD,
                        bgcolor=IPAColors.WHITE,
                        border=ft.border.all(1, IPAColors.LIGHT_GREY),
                        border_radius=IPASpacing.RADIUS_MD,
                    ),
                    # Action buttons
                    ft.Row(
                        [
                            create_secondary_button(
                                text="Back to Files",
                                on_click=lambda e: self.state_manager.navigate_to(
                                    AppConstants.SCREEN_FILE_SELECTION
                                ),
                                icon=ft.Icons.ARROW_BACK,
                            ),
                            create_primary_button(
                                text="Start Analysis",
                                on_click=self._handle_start_analysis,
                                icon=ft.Icons.PLAY_ARROW,
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                ],
                spacing=IPASpacing.LG,
                scroll=ft.ScrollMode.AUTO,
            ),
            padding=IPASpacing.XL,
            expand=True,
        )

    def _build_detection_method_section(
        self,
        method_id: str,
        title: str,
        description: str,
        checkbox: ft.Checkbox,
        is_expanded: bool,
    ):
        """Build an expandable detection method section."""

        def toggle_expand(e):
            # Toggle the expansion state
            if method_id == "column_name":
                self.column_name_expanded = not self.column_name_expanded
            elif method_id == "format_pattern":
                self.format_pattern_expanded = not self.format_pattern_expanded
            elif method_id == "sparsity":
                self.sparsity_expanded = not self.sparsity_expanded
            elif method_id == "location":
                self.location_expanded = not self.location_expanded
            elif method_id == "presidio":
                self.presidio_expanded = not self.presidio_expanded

            # Rebuild the detection methods container
            self._build_all_detection_methods()
            self.page.update()

        # Header with checkbox and toggle
        header = ft.Container(
            content=ft.Row(
                [
                    ft.Row(
                        [
                            checkbox,
                            ft.Text(
                                title,
                                size=IPATypography.BODY_LARGE,
                                weight=ft.FontWeight.W_500,
                                color=IPAColors.CHARCOAL,
                            ),
                        ],
                        spacing=IPASpacing.XS,
                    ),
                    ft.IconButton(
                        icon=ft.Icons.EXPAND_MORE
                        if not is_expanded
                        else ft.Icons.EXPAND_LESS,
                        icon_color=IPAColors.DARK_GREY,
                        on_click=toggle_expand,
                    ),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            ),
            padding=IPASpacing.SM,
            bgcolor=IPAColors.LIGHT_GREY,
            border_radius=IPASpacing.RADIUS_SM,
        )

        # Expanded content with detailed settings
        expanded_content = None
        if is_expanded:
            expanded_content = ft.Container(
                content=ft.Column(
                    [
                        ft.Text(
                            description,
                            size=IPATypography.BODY_SMALL,
                            color=IPAColors.DARK_GREY,
                        ),
                        self._get_method_settings(method_id),
                    ],
                    spacing=IPASpacing.SM,
                ),
                padding=IPASpacing.SM,
                bgcolor=IPAColors.WHITE,
                border=ft.border.all(1, IPAColors.LIGHT_GREY),
                border_radius=IPASpacing.RADIUS_SM,
            )

        # Return the complete section
        section_content = [header]
        if expanded_content:
            section_content.append(expanded_content)

        return ft.Column(section_content, spacing=IPASpacing.XS)

    def _build_all_detection_methods(self):
        """Build all detection method sections and update the container."""
        methods = [
            (
                "column_name",
                "Column Name/Label Analysis",
                "Analyzes column headers against restricted word lists for data collection variables, location identifiers, personal identifiers, and sensitive account information.",
                self.column_name_check,
                self.column_name_expanded,
            ),
            (
                "format_pattern",
                "Format Pattern Detection",
                "Identifies structured data patterns like phone numbers, emails, dates, and social security numbers using regex patterns.",
                self.format_pattern_check,
                self.format_pattern_expanded,
            ),
            (
                "sparsity",
                "Sparsity Analysis",
                "Flags columns where most values are unique, indicating potential open-ended responses or identifiers.",
                self.sparsity_check,
                self.sparsity_expanded,
            ),
            (
                "presidio",
                "AI-Powered Presidio Engine",
                "Uses Microsoft's Presidio ML models for advanced entity recognition and context-aware PII detection.",
                self.presidio_check,
                self.presidio_expanded,
            ),
            (
                "location",
                "Location Population Checks (GeoNames API Required)",
                "Cross-references location names against population databases to identify small communities (requires API access).",
                self.location_check,
                self.location_expanded,
            ),
        ]

        # Clear existing controls
        self.detection_methods_container.controls.clear()

        # Add all detection method sections
        for method_id, title, description, checkbox, is_expanded in methods:
            section = self._build_detection_method_section(
                method_id, title, description, checkbox, is_expanded
            )
            self.detection_methods_container.controls.append(section)

    def _get_method_settings(self, method_id: str):
        """Get detailed settings for each detection method."""
        if method_id == "column_name":
            # Create value display text
            fuzzy_value_text = ft.Text(
                "0.8 (80%)", size=IPATypography.BODY_SMALL, color=IPAColors.CHARCOAL
            )

            # Create fuzzy threshold slider (initially enabled based on default "fuzzy" value)
            fuzzy_threshold = ft.Slider(
                label="Fuzzy Match Threshold",
                value=0.8,
                min=0.5,
                max=1.0,
                divisions=10,
                width=200,
                disabled=False,  # Enabled by default since "fuzzy" is selected
            )

            def on_fuzzy_threshold_change(e):
                value = e.control.value
                fuzzy_value_text.value = f"{value:.1f} ({value * 100:.0f}%)"
                self.page.update()

            fuzzy_threshold.on_change = on_fuzzy_threshold_change

            def on_matching_type_change(e):
                # Enable/disable fuzzy threshold based on matching type
                matching_type = e.control.value
                fuzzy_threshold.disabled = matching_type == "strict"
                if matching_type == "strict":
                    fuzzy_value_text.value = "N/A (Strict mode)"
                else:
                    fuzzy_value_text.value = f"{fuzzy_threshold.value:.1f} ({fuzzy_threshold.value * 100:.0f}%)"
                self.page.update()

            matching_dropdown = ft.Dropdown(
                label="Matching Type",
                value="fuzzy",
                options=[
                    ft.dropdown.Option("strict", "Strict (Exact matches only)"),
                    ft.dropdown.Option("fuzzy", "Fuzzy (Allow similar terms)"),
                    ft.dropdown.Option("both", "Both (Strict + Fuzzy)"),
                ],
                width=250,
                on_change=on_matching_type_change,
            )

            return ft.Column(
                [
                    ft.Text(
                        "Matching Settings:",
                        size=IPATypography.BODY_SMALL,
                        weight=ft.FontWeight.W_500,
                    ),
                    matching_dropdown,
                    ft.Row(
                        [
                            fuzzy_threshold,
                            fuzzy_value_text,
                        ],
                        alignment=ft.MainAxisAlignment.START,
                        spacing=IPASpacing.SM,
                    ),
                ],
                spacing=IPASpacing.XS,
            )

        elif method_id == "format_pattern":
            confidence_value_text = ft.Text(
                "0.7 (70%)", size=IPATypography.BODY_SMALL, color=IPAColors.CHARCOAL
            )

            confidence_slider = ft.Slider(
                label="Detection Confidence",
                value=0.7,
                min=0.5,
                max=1.0,
                divisions=10,
                width=200,
            )

            def on_confidence_change(e):
                value = e.control.value
                confidence_value_text.value = f"{value:.1f} ({value * 100:.0f}%)"
                self.page.update()

            confidence_slider.on_change = on_confidence_change

            return ft.Column(
                [
                    ft.Text(
                        "Pattern Types:",
                        size=IPATypography.BODY_SMALL,
                        weight=ft.FontWeight.W_500,
                    ),
                    ft.Row(
                        [
                            ft.Checkbox(label="Phone Numbers", value=True),
                            ft.Checkbox(label="Email Addresses", value=True),
                        ],
                        spacing=IPASpacing.SM,
                    ),
                    ft.Row(
                        [
                            ft.Checkbox(label="Social Security Numbers", value=True),
                            ft.Checkbox(label="Date Formats", value=True),
                        ],
                        spacing=IPASpacing.SM,
                    ),
                    ft.Row(
                        [
                            confidence_slider,
                            confidence_value_text,
                        ],
                        alignment=ft.MainAxisAlignment.START,
                        spacing=IPASpacing.SM,
                    ),
                ],
                spacing=IPASpacing.XS,
            )

        elif method_id == "sparsity":
            uniqueness_value_text = ft.Text(
                "0.8 (80%)", size=IPATypography.BODY_SMALL, color=IPAColors.CHARCOAL
            )
            min_entries_value_text = ft.Text(
                "10 entries", size=IPATypography.BODY_SMALL, color=IPAColors.CHARCOAL
            )

            uniqueness_slider = ft.Slider(
                label="Uniqueness Threshold",
                value=0.8,
                min=0.5,
                max=1.0,
                divisions=10,
                width=200,
            )

            min_entries_slider = ft.Slider(
                label="Minimum Entries Required",
                value=10,
                min=5,
                max=100,
                divisions=19,
                width=200,
            )

            def on_uniqueness_change(e):
                value = e.control.value
                uniqueness_value_text.value = f"{value:.1f} ({value * 100:.0f}%)"
                self.page.update()

            def on_min_entries_change(e):
                value = int(e.control.value)
                min_entries_value_text.value = f"{value} entries"
                self.page.update()

            uniqueness_slider.on_change = on_uniqueness_change
            min_entries_slider.on_change = on_min_entries_change

            return ft.Column(
                [
                    ft.Text(
                        "Sparsity Thresholds:",
                        size=IPATypography.BODY_SMALL,
                        weight=ft.FontWeight.W_500,
                    ),
                    ft.Row(
                        [
                            uniqueness_slider,
                            uniqueness_value_text,
                        ],
                        alignment=ft.MainAxisAlignment.START,
                        spacing=IPASpacing.SM,
                    ),
                    ft.Row(
                        [
                            min_entries_slider,
                            min_entries_value_text,
                        ],
                        alignment=ft.MainAxisAlignment.START,
                        spacing=IPASpacing.SM,
                    ),
                ],
                spacing=IPASpacing.XS,
            )

        elif method_id == "location":
            population_value_text = ft.Text(
                "50,000 people", size=IPATypography.BODY_SMALL, color=IPAColors.CHARCOAL
            )

            population_slider = ft.Slider(
                label="Small Population Threshold",
                value=50000,
                min=1000,
                max=100000,
                divisions=99,
                width=200,
            )

            def on_population_change(e):
                value = int(e.control.value)
                population_value_text.value = f"{value:,} people"
                self.page.update()

            population_slider.on_change = on_population_change

            # API Key status display - check if API key is configured
            has_api_key = bool(self.state_manager.state.geonames_api_key)

            if has_api_key:
                api_status = ft.Container(
                    content=ft.Row(
                        [
                            ft.Icon(
                                ft.Icons.CHECK_CIRCLE, color=IPAColors.SUCCESS, size=16
                            ),
                            ft.Text(
                                "API Key configured",
                                size=IPATypography.BODY_SMALL,
                                color=IPAColors.SUCCESS,
                            ),
                        ],
                        spacing=IPASpacing.XS,
                    ),
                    padding=IPASpacing.SM,
                    bgcolor=IPAColors.SUCCESS + "20",  # 20% opacity
                    border_radius=IPASpacing.RADIUS_SM,
                )
            else:
                api_status = ft.Container(
                    content=ft.Row(
                        [
                            ft.Icon(
                                ft.Icons.WARNING, color=IPAColors.RED_ORANGE, size=16
                            ),
                            ft.Text(
                                "No API Key configured",
                                size=IPATypography.BODY_SMALL,
                                color=IPAColors.RED_ORANGE,
                            ),
                        ],
                        spacing=IPASpacing.XS,
                    ),
                    padding=IPASpacing.SM,
                    bgcolor=IPAColors.RED_ORANGE + "20",  # 20% opacity
                    border_radius=IPASpacing.RADIUS_SM,
                )

            # Information about getting API key with conditional button
            if has_api_key:
                # Show update option when API key exists
                api_info = ft.Container(
                    content=ft.Column(
                        [
                            ft.Text(
                                "API Key Information:",
                                size=IPATypography.BODY_SMALL,
                                weight=ft.FontWeight.W_500,
                            ),
                            ft.Text(
                                "✅ GeoNames API key is configured",
                                size=IPATypography.BODY_SMALL,
                            ),
                            ft.Text(
                                "• Free accounts: 1,000 requests/hour",
                                size=IPATypography.BODY_SMALL,
                            ),
                            # Update API Key button
                            ft.Container(
                                content=ft.ElevatedButton(
                                    text="Update API Key",
                                    icon=ft.Icons.EDIT,
                                    on_click=self._handle_add_api_key,
                                    style=ft.ButtonStyle(
                                        bgcolor=IPAColors.DARK_BLUE,
                                        color=IPAColors.WHITE,
                                    ),
                                ),
                                margin=ft.margin.only(top=IPASpacing.SM),
                            ),
                        ],
                        spacing=IPASpacing.XS,
                    ),
                    padding=IPASpacing.SM,
                    bgcolor=IPAColors.LIGHT_GREY,
                    border_radius=IPASpacing.RADIUS_SM,
                )
            else:
                # Show setup option when no API key
                api_info = ft.Container(
                    content=ft.Column(
                        [
                            ft.Text(
                                "API Key Information:",
                                size=IPATypography.BODY_SMALL,
                                weight=ft.FontWeight.W_500,
                            ),
                            ft.Text(
                                "• Register at: https://www.geonames.org/login",
                                size=IPATypography.BODY_SMALL,
                            ),
                            ft.Text(
                                "• Free account allows 1,000 requests/hour",
                                size=IPATypography.BODY_SMALL,
                            ),
                            ft.Text(
                                "• Your username is your API key",
                                size=IPATypography.BODY_SMALL,
                            ),
                            # Add API Key button
                            ft.Container(
                                content=ft.ElevatedButton(
                                    text="Add API Key",
                                    icon=ft.Icons.KEY,
                                    on_click=self._handle_add_api_key,
                                    style=ft.ButtonStyle(
                                        bgcolor=IPAColors.IPA_GREEN,
                                        color=IPAColors.WHITE,
                                    ),
                                ),
                                margin=ft.margin.only(top=IPASpacing.SM),
                            ),
                        ],
                        spacing=IPASpacing.XS,
                    ),
                    padding=IPASpacing.SM,
                    bgcolor=IPAColors.LIGHT_GREY,
                    border_radius=IPASpacing.RADIUS_SM,
                )

            return ft.Column(
                [
                    ft.Text(
                        "Population Lookup:",
                        size=IPATypography.BODY_SMALL,
                        weight=ft.FontWeight.W_500,
                    ),
                    api_status,
                    api_info,
                    ft.Row(
                        [
                            population_slider,
                            population_value_text,
                        ],
                        alignment=ft.MainAxisAlignment.START,
                        spacing=IPASpacing.SM,
                    ),
                ],
                spacing=IPASpacing.XS,
            )

        elif method_id == "presidio":
            presidio_confidence_value_text = ft.Text(
                "0.8 (80%)", size=IPATypography.BODY_SMALL, color=IPAColors.CHARCOAL
            )

            confidence_slider = ft.Slider(
                label="Confidence Threshold",
                value=0.8,
                min=0.5,
                max=1.0,
                divisions=10,
                width=200,
            )

            def on_presidio_confidence_change(e):
                value = e.control.value
                presidio_confidence_value_text.value = (
                    f"{value:.1f} ({value * 100:.0f}%)"
                )
                self.page.update()

            confidence_slider.on_change = on_presidio_confidence_change

            return ft.Column(
                [
                    ft.Text(
                        "Presidio Settings:",
                        size=IPATypography.BODY_SMALL,
                        weight=ft.FontWeight.W_500,
                    ),
                    ft.Dropdown(
                        label="Language Model",
                        value="en_core_web_sm",
                        options=[
                            ft.dropdown.Option("en_core_web_sm", "English (Small)"),
                            ft.dropdown.Option("en_core_web_md", "English (Medium)"),
                            ft.dropdown.Option("en_core_web_lg", "English (Large)"),
                        ],
                        width=250,
                    ),
                    ft.Row(
                        [
                            confidence_slider,
                            presidio_confidence_value_text,
                        ],
                        alignment=ft.MainAxisAlignment.START,
                        spacing=IPASpacing.SM,
                    ),
                    ft.Row(
                        [
                            ft.Checkbox(label="Person Names", value=True),
                            ft.Checkbox(label="Organizations", value=True),
                        ],
                        spacing=IPASpacing.SM,
                    ),
                ],
                spacing=IPASpacing.XS,
            )

        return ft.Text(
            "No additional settings",
            size=IPATypography.BODY_SMALL,
            color=IPAColors.DARK_GREY,
        )

    def _set_preset(self, preset_type: str):
        """Set detection method presets."""
        # Update preset button styles
        if preset_type == "quick":
            self.preset_quick.style.bgcolor = IPAColors.IPA_GREEN
            self.preset_quick.style.color = IPAColors.WHITE
            self.preset_balanced.style.bgcolor = IPAColors.LIGHT_GREY
            self.preset_balanced.style.color = IPAColors.CHARCOAL
            self.preset_thorough.style.bgcolor = IPAColors.LIGHT_GREY
            self.preset_thorough.style.color = IPAColors.CHARCOAL

            # Quick preset: Enable only basic methods
            self.column_name_check.value = True
            self.format_pattern_check.value = True
            self.sparsity_check.value = False
            self.location_check.value = False
            self.presidio_check.value = False

        elif preset_type == "balanced":
            self.preset_balanced.style.bgcolor = IPAColors.IPA_GREEN
            self.preset_balanced.style.color = IPAColors.WHITE
            self.preset_quick.style.bgcolor = IPAColors.LIGHT_GREY
            self.preset_quick.style.color = IPAColors.CHARCOAL
            self.preset_thorough.style.bgcolor = IPAColors.LIGHT_GREY
            self.preset_thorough.style.color = IPAColors.CHARCOAL

            # Balanced preset: Enable most methods
            self.column_name_check.value = True
            self.format_pattern_check.value = True
            self.sparsity_check.value = True
            self.location_check.value = False
            self.presidio_check.value = False

        elif preset_type == "thorough":
            self.preset_thorough.style.bgcolor = IPAColors.IPA_GREEN
            self.preset_thorough.style.color = IPAColors.WHITE
            self.preset_quick.style.bgcolor = IPAColors.LIGHT_GREY
            self.preset_quick.style.color = IPAColors.CHARCOAL
            self.preset_balanced.style.bgcolor = IPAColors.LIGHT_GREY
            self.preset_balanced.style.color = IPAColors.CHARCOAL

            # Thorough preset: Enable all methods
            self.column_name_check.value = True
            self.format_pattern_check.value = True
            self.sparsity_check.value = True
            self.location_check.value = True
            self.presidio_check.value = True

        self.page.update()

    def _handle_start_analysis(self, e):
        """Handle start analysis button click."""
        # Validate that at least one detection method is selected
        detection_methods_enabled = [
            self.column_name_check.value,
            self.format_pattern_check.value,
            self.sparsity_check.value,
            self.location_check.value,
            self.presidio_check.value,
        ]

        if not any(detection_methods_enabled):
            # Show error dialog
            def close_dialog(e):
                dialog.open = False
                self.page.update()

            dialog = ft.AlertDialog(
                modal=True,
                title=ft.Text("No Detection Methods Selected", color=IPAColors.ERROR),
                content=ft.Column(
                    [
                        ft.Icon(ft.Icons.WARNING, color=IPAColors.ERROR, size=48),
                        ft.Text(
                            "Please select at least one PII detection method before starting the analysis.",
                            text_align=ft.TextAlign.CENTER,
                        ),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    tight=True,
                ),
                actions=[
                    ft.TextButton("OK", on_click=close_dialog),
                ],
                actions_alignment=ft.MainAxisAlignment.END,
            )

            self.page.open(dialog)
            return

        # Collect configuration and save to state
        config = DetectionConfig(
            # Detection methods
            column_name_enabled=self.column_name_check.value,
            format_pattern_enabled=self.format_pattern_check.value,
            sparsity_enabled=self.sparsity_check.value,
            location_population_enabled=self.location_check.value,
            ai_text_enabled=self.presidio_check.value,
            # Configuration values (using defaults from DetectionConfig for now)
            sparsity_threshold=0.6,  # Default from DetectionConfig
            population_threshold=15000,  # Default from DetectionConfig
        )

        # Save configuration to state
        self.state_manager.update_state(
            detection_config=config,
        )

        # Show success message and navigate
        self.state_manager.add_success_message(
            "Configuration saved. Starting analysis..."
        )
        self.state_manager.navigate_to(AppConstants.SCREEN_PROGRESS)

    def _handle_add_api_key(self, e):
        """Handle Add API Key button click in Location Population section."""
        # Show API key input dialog
        api_key_field = ft.TextField(
            label="GeoNames API Key",
            hint_text="Enter your GeoNames username",
            width=350,
            value="",
        )

        def close_api_dialog(e=None):
            dialog.open = False
            self.page.update()

        def save_api_key(e):
            api_key = api_key_field.value.strip()
            if api_key:
                # Save API key securely (don't log the actual key!)
                # In real app, this would be stored securely in keychain/credential store
                self.state_manager.update_state(geonames_api_key=api_key)

                # Show success message
                self.state_manager.add_success_message("API key saved successfully!")
                close_api_dialog()

                # Rebuild the detection methods to show updated status
                self._build_all_detection_methods()
                self.page.update()
            else:
                self.state_manager.add_error_message("Please enter a valid API key")

        def test_api_key(e):
            api_key = api_key_field.value.strip()
            if not api_key:
                self.state_manager.add_error_message("Please enter an API key first")
                return

            # Test the API key with a simple GeoNames request
            import threading

            import requests

            def test_api():
                try:
                    # Simple test query to GeoNames API
                    test_url = f"http://api.geonames.org/searchJSON?q=London&maxRows=1&username={api_key}"
                    response = requests.get(test_url, timeout=10)

                    if response.status_code == 200:
                        data = response.json()
                        if "geonames" in data and len(data["geonames"]) > 0:
                            # API key works
                            self.state_manager.add_success_message(
                                "✅ API key is valid and working!"
                            )
                        else:
                            self.state_manager.add_error_message(
                                "API key may be invalid - no results returned"
                            )
                    else:
                        self.state_manager.add_error_message(
                            f"API test failed - HTTP {response.status_code}"
                        )

                except requests.exceptions.Timeout:
                    self.state_manager.add_error_message(
                        "API test timeout - please check internet connection"
                    )
                except requests.exceptions.RequestException:
                    self.state_manager.add_error_message(
                        "API test failed - network error"
                    )
                except Exception:
                    self.state_manager.add_error_message(
                        "API test failed - unexpected error"
                    )

            # Show testing message and run test
            self.state_manager.add_success_message("Testing API key...")
            threading.Thread(target=test_api, daemon=True).start()

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Configure GeoNames API Key", color=IPAColors.DARK_BLUE),
            content=ft.Container(
                content=ft.Column(
                    [
                        ft.Text(
                            "Location Population Check Configuration",
                            size=IPATypography.BODY_REGULAR,
                            weight=ft.FontWeight.W_500,
                        ),
                        ft.Text(
                            "Required for identifying small communities by population size",
                            size=IPATypography.BODY_SMALL,
                            color=IPAColors.DARK_GREY,
                        ),
                        api_key_field,
                        ft.Container(
                            content=ft.Column(
                                [
                                    ft.Text(
                                        "How to get your API key:",
                                        size=IPATypography.BODY_SMALL,
                                        weight=ft.FontWeight.W_500,
                                    ),
                                    ft.Text(
                                        "1. Register at: https://www.geonames.org/login",
                                        size=IPATypography.BODY_SMALL,
                                    ),
                                    ft.Text(
                                        "2. Your username is your API key",
                                        size=IPATypography.BODY_SMALL,
                                    ),
                                    ft.Text(
                                        "3. Free accounts: 1,000 requests/hour",
                                        size=IPATypography.BODY_SMALL,
                                    ),
                                ],
                                spacing=4,
                            ),
                            padding=IPASpacing.SM,
                            bgcolor=IPAColors.LIGHT_GREY,
                            border_radius=IPASpacing.RADIUS_SM,
                            margin=ft.margin.symmetric(vertical=IPASpacing.SM),
                        ),
                    ],
                    spacing=IPASpacing.SM,
                ),
                width=450,
                height=300,
            ),
            actions=[
                ft.TextButton("Cancel", on_click=close_api_dialog),
                ft.TextButton("Test", on_click=test_api_key),
                ft.ElevatedButton(
                    "Save",
                    on_click=save_api_key,
                    style=ft.ButtonStyle(
                        bgcolor=IPAColors.IPA_GREEN,
                        color=IPAColors.WHITE,
                    ),
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        self.page.open(dialog)

    def on_state_changed(self, state: AppState):
        """Handle state changes."""
        pass
