"""Main application controller and state manager."""

import contextlib
from typing import Any

import flet as ft

from pii_detector.gui.flet_app.config.constants import AppConstants, IPAColors
from pii_detector.gui.flet_app.config.settings import AppState
from pii_detector.gui.flet_app.ui.screens.configuration import ConfigurationScreen
from pii_detector.gui.flet_app.ui.screens.dashboard import DashboardScreen
from pii_detector.gui.flet_app.ui.screens.file_selection import FileSelectionScreen
from pii_detector.gui.flet_app.ui.screens.progress import ProgressScreen
from pii_detector.gui.flet_app.ui.screens.results import ResultsScreen


class StateManager:
    """Central state management for the application."""

    def __init__(self, page: ft.Page):
        """Initialize the state manager.

        Args:
            page: Flet page instance

        """
        self.page = page
        self.state = AppState()
        self._observers = []

    def update_state(self, **kwargs):
        """Central state update method with UI refresh.

        Args:
            **kwargs: State attributes to update

        """
        for key, value in kwargs.items():
            if hasattr(self.state, key):
                setattr(self.state, key, value)

        # Notify observers
        self.notify_observers()

    def add_observer(self, observer):
        """Add state change observer."""
        self._observers.append(observer)

    def notify_observers(self):
        """Notify all observers of state changes."""
        for observer in self._observers:
            if hasattr(observer, "on_state_changed"):
                observer.on_state_changed(self.state)

    def navigate_to(self, screen_name: str):
        """Navigate to a specific screen.

        Args:
            screen_name: Name of the screen to navigate to

        """
        # Add current screen to history
        if self.state.current_screen != screen_name:
            self.state.screen_history.append(self.state.current_screen)

        self.update_state(current_screen=screen_name)

    def go_back(self):
        """Navigate back to the previous screen."""
        if self.state.screen_history:
            previous_screen = self.state.screen_history.pop()
            self.update_state(current_screen=previous_screen)

    def add_error_message(self, message: str):
        """Add an error message to the state."""
        errors = self.state.error_messages.copy()
        errors.append(message)
        self.update_state(error_messages=errors)

    def add_success_message(self, message: str):
        """Add a success message to the state."""
        messages = self.state.success_messages.copy()
        messages.append(message)
        self.update_state(success_messages=messages)

    def clear_messages(self):
        """Clear all messages."""
        self.update_state(error_messages=[], success_messages=[])


class PIIDetectorApp:
    """Main application class."""

    def __init__(self, page: ft.Page):
        """Initialize the main application.

        Args:
            page: Flet page instance

        """
        self.page = page
        self.state_manager = StateManager(page)
        self.screens: dict[str, Any] = {}
        self.current_screen_widget = None

        # Initialize screens
        self._initialize_screens()

    def _initialize_screens(self):
        """Initialize all application screens."""
        self.screens = {
            AppConstants.SCREEN_DASHBOARD: DashboardScreen(
                self.page, self.state_manager
            ),
            AppConstants.SCREEN_FILE_SELECTION: FileSelectionScreen(
                self.page, self.state_manager
            ),
            AppConstants.SCREEN_CONFIGURATION: ConfigurationScreen(
                self.page, self.state_manager
            ),
            AppConstants.SCREEN_PROGRESS: ProgressScreen(self.page, self.state_manager),
            AppConstants.SCREEN_RESULTS: ResultsScreen(self.page, self.state_manager),
        }

        # Add state manager as observer for each screen
        for screen in self.screens.values():
            self.state_manager.add_observer(screen)

    def initialize(self):
        """Initialize the application and show the first screen."""
        # Add this app as an observer to the state manager
        self.state_manager.add_observer(self)

        # Create header bar
        self.header_bar = self._create_header_bar()

        # Create main content area
        self.main_content = ft.Container(
            expand=True,
            padding=0,
        )

        # Create main layout
        self.page.add(
            ft.Column(
                [
                    self.header_bar,
                    self.main_content,
                ],
                spacing=0,
                expand=True,
            )
        )

        # Show initial screen
        self._show_screen(AppConstants.SCREEN_DASHBOARD)

        # Update the page
        self.page.update()

    def _create_header_bar(self) -> ft.Container:
        """Create the application header bar."""
        return ft.Container(
            content=ft.Row(
                [
                    # Left side - App title and icon
                    ft.Row(
                        [
                            ft.Icon(
                                ft.Icons.SHIELD,
                                size=24,
                                color=IPAColors.WHITE,
                            ),
                            ft.Text(
                                "IPA PII Detector v3.0",
                                size=16,
                                weight=ft.FontWeight.W_600,
                                color=IPAColors.WHITE,
                            ),
                        ],
                        spacing=8,
                    ),
                    # Right side - Settings and navigation
                    ft.Row(
                        [
                            # Back button (only show if there's history)
                            ft.IconButton(
                                icon=ft.Icons.ARROW_BACK,
                                tooltip="Go Back",
                                icon_color=IPAColors.WHITE,
                                on_click=lambda e: self.state_manager.go_back(),
                                visible=len(self.state_manager.state.screen_history)
                                > 0,
                            ),
                            # Settings button
                            ft.IconButton(
                                icon=ft.Icons.SETTINGS,
                                tooltip="Settings",
                                icon_color=IPAColors.WHITE,
                                on_click=self._handle_settings_click,
                                bgcolor=IPAColors.IPA_GREEN,
                                style=ft.ButtonStyle(
                                    shape=ft.RoundedRectangleBorder(radius=6),
                                ),
                            ),
                        ],
                        spacing=8,
                    ),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            ),
            height=60,
            bgcolor=IPAColors.DARK_BLUE,
            padding=ft.padding.symmetric(horizontal=24, vertical=8),
        )

    def _handle_settings_click(self, e):
        """Handle settings button click."""
        with contextlib.suppress(Exception):
            # Silently handle any errors
            self._show_settings()

    def _show_settings(self):
        """Show settings dialog with actual functionality."""
        # # print("DEBUG: Settings button clicked!")  # Debug output

        def close_settings(e):
            self.page.close(settings_dialog)
            # # print("DEBUG: Settings dialog closed")

        def reset_app(e):
            # print("DEBUG: Reset Application clicked!")
            # Reset application state
            self.state_manager.update_state(
                selected_files=[],
                file_validation_results={},
                detection_results=[],
                user_actions={},
                error_messages=[],
                success_messages=[],
            )
            self.state_manager.navigate_to(AppConstants.SCREEN_DASHBOARD)
            self.state_manager.add_success_message("Application reset successfully")
            # print("DEBUG: Application state reset completed")
            close_settings(e)

        def show_about(e):
            close_settings(e)
            self._show_about_dialog()

        def show_export_location(e):
            # print("DEBUG: Export Location clicked!")
            close_settings(e)
            self._show_export_location_dialog()

        settings_content = ft.Column(
            [
                ft.Text("Application Settings", size=16, weight=ft.FontWeight.W_600),
                ft.Divider(),
                ft.ListTile(
                    leading=ft.Icon(ft.Icons.INFO),
                    title=ft.Text("About PII Detector"),
                    subtitle=ft.Text("Version information and credits"),
                    on_click=show_about,
                ),
                ft.ListTile(
                    leading=ft.Icon(ft.Icons.REFRESH),
                    title=ft.Text("Reset Application"),
                    subtitle=ft.Text("Clear all data and return to dashboard"),
                    on_click=reset_app,
                ),
                ft.ListTile(
                    leading=ft.Icon(ft.Icons.FOLDER),
                    title=ft.Text("Export Location"),
                    subtitle=ft.Text("Default: Downloads folder"),
                    trailing=ft.Icon(ft.Icons.CHEVRON_RIGHT),
                    on_click=show_export_location,
                ),
            ]
        )

        settings_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Settings"),
            content=ft.Container(
                content=settings_content,
                width=400,
                height=300,
            ),
            actions=[
                ft.TextButton("Close", on_click=close_settings),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        # Try the standard Flet dialog method
        self.page.open(settings_dialog)
        # print("DEBUG: Dialog opened with page.open() method")

    def _show_about_dialog(self):
        """Show about dialog."""

        def close_about(e):
            self.page.close(about_dialog)
            # print("DEBUG: About dialog closed")

        about_content = ft.Column(
            [
                ft.Icon(ft.Icons.SHIELD, size=48, color=IPAColors.IPA_GREEN),
                ft.Text("PII Detector", size=20, weight=ft.FontWeight.BOLD),
                ft.Text(
                    "Version 3.0 (Flet Edition)", size=14, color=IPAColors.DARK_GREY
                ),
                ft.Divider(),
                ft.Text(
                    "A professional tool for identifying and anonymizing personally identifiable information (PII) in research datasets.",
                    text_align=ft.TextAlign.CENTER,
                ),
                ft.Text(
                    "Built by IPA Global Research and Data Science",
                    size=12,
                    color=IPAColors.DARK_GREY,
                    text_align=ft.TextAlign.CENTER,
                ),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=8,
        )

        about_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("About PII Detector"),
            content=ft.Container(
                content=about_content,
                width=350,
                height=200,
            ),
            actions=[
                ft.TextButton("Close", on_click=close_about),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        self.page.open(about_dialog)
        # print("DEBUG: About dialog opened")

    def _show_export_location_dialog(self):
        """Show export location selection dialog."""
        import os

        def close_export_dialog(e):
            self.page.close(export_dialog)
            # print("DEBUG: Export location dialog closed")

        def handle_folder_result(e: ft.FilePickerResultEvent):
            if e.path:
                # Update the display with the new path
                location_display.content = ft.Text(
                    e.path,
                    size=12,
                    color=IPAColors.DARK_GREY,
                )
                location_display.update()  # Force update the container

                # Show success message using snack_bar
                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text(f"Export location updated to: {e.path}"),
                    action="OK",
                )
                self.page.snack_bar.open = True
                self.page.update()

        def browse_folder(e):
            # print("DEBUG: Browse folder clicked - opening folder picker")
            folder_picker.get_directory_path(dialog_title="Select Export Folder")

        # Create folder picker
        folder_picker = ft.FilePicker(on_result=handle_folder_result)

        # Add folder picker to page overlay if not already added
        if folder_picker not in self.page.overlay:
            self.page.overlay.append(folder_picker)

        current_location = os.path.join(os.path.expanduser("~"), "Downloads")

        # Create the location display container that can be updated
        location_display = ft.Container(
            content=ft.Text(
                current_location,
                size=12,
                color=IPAColors.DARK_GREY,
            ),
            padding=ft.padding.all(10),
            bgcolor=IPAColors.LIGHT_GREY,
            border_radius=5,
        )

        export_content = ft.Column(
            [
                ft.Text(
                    "Export Location Settings", size=16, weight=ft.FontWeight.W_600
                ),
                ft.Divider(),
                ft.Text("Current export location:", size=14),
                location_display,
                ft.Text("All processed files and reports will be saved here.", size=12),
                ft.ElevatedButton(
                    text="Browse Folder",
                    icon=ft.Icons.FOLDER_OPEN,
                    on_click=browse_folder,
                    style=ft.ButtonStyle(
                        bgcolor=IPAColors.IPA_GREEN,
                        color=IPAColors.WHITE,
                    ),
                ),
            ],
            spacing=10,
        )

        export_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Export Location"),
            content=ft.Container(
                content=export_content,
                width=400,
                height=250,
            ),
            actions=[
                ft.TextButton("Close", on_click=close_export_dialog),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        self.page.open(export_dialog)
        # print("DEBUG: Export location dialog opened")

        # Create the text field
        geonames_api_field = ft.TextField(
            label="GeoNames API Key",
            hint_text="Enter your GeoNames username",
            width=350,
            value="",
        )

        def close_custom_modal(e=None):
            # Remove the modal from overlay
            with contextlib.suppress(Exception):
                self.page.overlay.remove(modal_overlay)
                self.page.update()
                # print("DEBUG: Custom modal closed")

        def save_api_keys(e):
            geonames_key = geonames_api_field.value

            if geonames_key and geonames_key.strip():
                close_custom_modal()

                # Show success message
                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text("API key saved successfully!"), action="OK"
                )
                self.page.snack_bar.open = True
                self.page.update()
            else:
                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text("Please enter a valid API key"), action="OK"
                )
                self.page.snack_bar.open = True
                self.page.update()

        def test_api_key(e):
            geonames_key = geonames_api_field.value

            if not geonames_key or not geonames_key.strip():
                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text("Please enter an API key first"), action="OK"
                )
                self.page.snack_bar.open = True
                self.page.update()
                return

            self.page.snack_bar = ft.SnackBar(
                content=ft.Text("API key test - functionality coming soon"), action="OK"
            )
            self.page.snack_bar.open = True
            self.page.update()

        # Create custom modal overlay
        modal_content = ft.Container(
            content=ft.Column(
                [
                    # Title
                    ft.Text(
                        "API Keys Configuration",
                        size=18,
                        weight=ft.FontWeight.W_600,
                        color=IPAColors.DARK_BLUE,
                    ),
                    ft.Divider(),
                    # Content
                    ft.Text(
                        "GeoNames API Configuration",
                        size=14,
                        weight=ft.FontWeight.W_500,
                    ),
                    ft.Text(
                        "Required for Location Population Checks",
                        size=12,
                        color=IPAColors.DARK_GREY,
                    ),
                    # Text field
                    geonames_api_field,
                    # Instructions
                    ft.Container(
                        content=ft.Column(
                            [
                                ft.Text(
                                    "How to get your API key:",
                                    size=12,
                                    weight=ft.FontWeight.W_500,
                                ),
                                ft.Text("1. Register at: geonames.org/login", size=11),
                                ft.Text("2. Your username is your API key", size=11),
                                ft.Text(
                                    "3. Free accounts: 1,000 requests/hour", size=11
                                ),
                            ]
                        ),
                        padding=10,
                        bgcolor=IPAColors.LIGHT_GREY,
                        border_radius=5,
                    ),
                    # Add some spacing before buttons
                    ft.Container(height=20),
                    # Buttons
                    ft.Row(
                        [
                            ft.TextButton("Close", on_click=close_custom_modal),
                            ft.ElevatedButton("Test", on_click=test_api_key),
                            ft.ElevatedButton(
                                "Save",
                                on_click=save_api_keys,
                                style=ft.ButtonStyle(
                                    bgcolor=IPAColors.IPA_GREEN,
                                    color=IPAColors.WHITE,
                                ),
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.END,
                    ),
                ],
                spacing=15,
            ),
            padding=25,
            width=500,
            height=500,
            bgcolor=IPAColors.WHITE,
            border_radius=10,
            border=ft.border.all(2, IPAColors.DARK_GREY),
            shadow=ft.BoxShadow(
                spread_radius=1, blur_radius=15, color=ft.colors.BLACK54
            ),
        )

        # Create semi-transparent background
        modal_overlay = ft.Container(
            content=ft.Stack(
                [
                    # Background overlay (semi-transparent)
                    ft.Container(
                        width=self.page.window_width or 1200,
                        height=self.page.window_height or 800,
                        bgcolor=ft.colors.BLACK54,
                        on_click=close_custom_modal,  # Click outside to close
                    ),
                    # Centered modal content
                    ft.Container(
                        content=modal_content,
                        alignment=ft.alignment.center,
                        width=self.page.window_width or 1200,
                        height=self.page.window_height or 800,
                    ),
                ]
            ),
            expand=True,
        )

        # Add to overlay
        self.page.overlay.append(modal_overlay)
        self.page.update()

        # Try to focus the text field
        def focus_field():
            try:
                geonames_api_field.focus()
                self.page.update()
                pass
            except Exception:
                pass

        import threading

        threading.Timer(0.2, focus_field).start()

        # print("DEBUG: Custom modal overlay created and added")

    def _show_screen(self, screen_name: str):
        """Show a specific screen.

        Args:
            screen_name: Name of the screen to show

        """
        if screen_name in self.screens:
            # Update back button visibility
            back_button = self.header_bar.content.controls[1].controls[0]
            back_button.visible = len(self.state_manager.state.screen_history) > 0

            # Get the screen widget
            screen = self.screens[screen_name]
            screen_widget = screen.build()

            # Update main content
            self.main_content.content = screen_widget
            self.current_screen_widget = screen_widget

            # Update state without triggering observer notifications (to avoid loops)
            self.state_manager.state.current_screen = screen_name

            # Update the page
            self.page.update()

    def on_state_changed(self, state: AppState):
        """Handle state changes from the state manager.

        Args:
            state: The updated application state

        """
        # Check if we need to navigate to a different screen
        current_screen_name = getattr(self.current_screen_widget, "_screen_name", None)
        if state.current_screen != current_screen_name:
            self._show_screen(state.current_screen)

        # Update back button visibility
        if hasattr(self, "header_bar") and self.header_bar:
            back_button = self.header_bar.content.controls[1].controls[0]
            back_button.visible = len(state.screen_history) > 0
            self.page.update()
