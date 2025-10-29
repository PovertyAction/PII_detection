"""Progress screen for tracking PII detection analysis."""

import contextlib
import threading
import time

import flet as ft

from pii_detector.gui.flet_app.backend_adapter import (
    BackgroundProcessor,
    PIIDetectionAdapter,
)
from pii_detector.gui.flet_app.config.constants import (
    AppConstants,
    IPAColors,
    IPASpacing,
    IPATypography,
)
from pii_detector.gui.flet_app.config.settings import AppState
from pii_detector.gui.flet_app.ui.components.buttons import (
    create_primary_button,
    create_secondary_button,
)


class ProgressScreen:
    """Progress screen implementation for tracking analysis progress."""

    def __init__(self, page: ft.Page, state_manager):
        """Initialize the progress screen.

        Args:
            page: Flet page instance
            state_manager: Application state manager

        """
        self.page = page
        self.state_manager = state_manager
        self._screen_name = AppConstants.SCREEN_PROGRESS

        # Progress tracking
        self.overall_progress_bar = None
        self.current_task_text = None
        self.progress_log = None
        self.cancel_button = None
        self.view_results_button = None
        self.progress_percentage_text = None

        # Analysis state
        self.is_analysis_running = False
        self.analysis_cancelled = False
        self.analysis_complete = False
        self.current_step = 0
        self.total_steps = 0
        self.progress_messages = []

        # Backend integration
        self.adapter = PIIDetectionAdapter()
        self.background_processor = BackgroundProcessor(self.adapter)

        # Progress log storage for copying
        self.progress_messages = []

    def build(self) -> ft.Container:
        """Build the progress screen."""
        return ft.Container(
            content=ft.Column(
                [
                    # Header
                    self._build_header(),
                    # Progress Section
                    self._build_progress_section(),
                    # Progress Log
                    self._build_progress_log(),
                    # Action Buttons
                    self._build_action_buttons(),
                ],
                spacing=IPASpacing.LG,
            ),
            padding=IPASpacing.XL,
            expand=True,
        )

    def _build_header(self) -> ft.Column:
        """Build the screen header."""
        return ft.Column(
            [
                ft.Text(
                    "Analysis Progress",
                    size=IPATypography.HEADER_2,
                    weight=ft.FontWeight.W_600,
                    color=IPAColors.DARK_BLUE,
                ),
                ft.Text(
                    "Analyzing your dataset for PII detection and preparing anonymized results.",
                    size=IPATypography.BODY_REGULAR,
                    color=IPAColors.CHARCOAL,
                ),
            ],
            spacing=IPASpacing.SM,
        )

    def _build_progress_section(self) -> ft.Container:
        """Build the progress tracking section."""
        # Overall progress bar
        self.overall_progress_bar = ft.ProgressBar(
            value=0,
            color=IPAColors.IPA_GREEN,
            bgcolor=IPAColors.LIGHT_GREY,
            height=8,
        )

        # Current task indicator
        self.current_task_text = ft.Text(
            "Preparing analysis...",
            size=IPATypography.BODY_REGULAR,
            color=IPAColors.CHARCOAL,
            weight=ft.FontWeight.W_500,
        )

        # Progress percentage text
        self.progress_percentage_text = ft.Text(
            "0%",
            size=IPATypography.BODY_REGULAR,
            color=IPAColors.DARK_GREY,
        )

        return ft.Container(
            content=ft.Column(
                [
                    ft.Text(
                        "Overall Progress",
                        size=IPATypography.BODY_LARGE,
                        weight=ft.FontWeight.W_600,
                        color=IPAColors.CHARCOAL,
                    ),
                    self.overall_progress_bar,
                    ft.Row(
                        [
                            self.current_task_text,
                            self.progress_percentage_text,
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                ],
                spacing=IPASpacing.SM,
            ),
            padding=IPASpacing.MD,
            bgcolor=IPAColors.WHITE,
            border=ft.border.all(1, IPAColors.DARK_GREY),
            border_radius=IPASpacing.RADIUS_MD,
        )

    def _build_progress_log(self) -> ft.Container:
        """Build the progress log section."""
        self.progress_log = ft.Column(
            [
                ft.Text(
                    "Ready to start analysis",
                    size=IPATypography.BODY_SMALL,
                    color=IPAColors.DARK_GREY,
                ),
            ],
            spacing=IPASpacing.XS,
            scroll=ft.ScrollMode.AUTO,
        )

        # Add initial message to progress messages list
        self.progress_messages = ["Ready to start analysis"]

        return ft.Container(
            content=ft.Column(
                [
                    ft.Row(
                        [
                            ft.Text(
                                "Progress Log",
                                size=IPATypography.BODY_LARGE,
                                weight=ft.FontWeight.W_600,
                                color=IPAColors.CHARCOAL,
                            ),
                            ft.IconButton(
                                icon=ft.Icons.COPY,
                                tooltip="Copy progress log to clipboard",
                                icon_size=20,
                                on_click=self._handle_copy_log,
                                style=ft.ButtonStyle(
                                    color=IPAColors.DARK_BLUE,
                                ),
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    ft.Container(
                        content=self.progress_log,
                        height=200,
                        padding=IPASpacing.SM,
                        bgcolor=IPAColors.WHITE,
                        border=ft.border.all(1, IPAColors.DARK_GREY),
                        border_radius=IPASpacing.RADIUS_SM,
                    ),
                ],
                spacing=IPASpacing.SM,
            ),
        )

    def _build_action_buttons(self) -> ft.Row:
        """Build the action buttons."""
        self.cancel_button = create_secondary_button(
            text="Cancel Analysis",
            on_click=self._handle_cancel_analysis,
            icon=ft.Icons.CANCEL,
            disabled=False,
        )

        self.view_results_button = create_primary_button(
            text="View Results",
            on_click=self._handle_view_results,
            icon=ft.Icons.VISIBILITY,
            disabled=True,
        )

        return ft.Row(
            [
                create_secondary_button(
                    text="Back to Configuration",
                    on_click=self._handle_back_to_config,
                    icon=ft.Icons.ARROW_BACK,
                    disabled=False,
                ),
                self.cancel_button,
                self.view_results_button,
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        )

    def _handle_cancel_analysis(self, e):
        """Handle analysis cancellation."""
        if self.is_analysis_running:
            self.analysis_cancelled = True
            self._add_log_message("Analysis cancelled by user", IPAColors.WARNING)
            self._update_current_task("Cancelling analysis...")
            if self.cancel_button:
                self.cancel_button.disabled = True
            with contextlib.suppress(Exception):
                # Ignore if page is no longer available
                self.page.update()

            # Cancel the real backend processing
            self.background_processor.cancel_analysis()
            threading.Thread(
                target=self._handle_cancellation_cleanup, daemon=True
            ).start()

    def _handle_view_results(self, e):
        """Handle view results button click."""
        if self.analysis_complete:
            # Navigate to results screen
            self.state_manager.add_success_message("Analysis completed successfully!")
            self.state_manager.navigate_to(AppConstants.SCREEN_RESULTS)

    def _handle_back_to_config(self, e):
        """Handle back to configuration button click."""
        if not self.is_analysis_running:
            self.state_manager.navigate_to(AppConstants.SCREEN_CONFIGURATION)

    def _handle_copy_log(self, e):
        """Handle copying the progress log to clipboard."""
        try:
            # Create a formatted log text
            log_text = "\n".join(self.progress_messages)

            # Add header with timestamp and analysis info
            current_time = time.strftime("%Y-%m-%d %H:%M:%S")
            header = f"PII Detection Analysis Progress Log\nGenerated: {current_time}\n{'-' * 50}\n\n"
            full_text = header + log_text

            # Copy to clipboard using Flet's clipboard functionality
            self.page.set_clipboard(full_text)

            # Show feedback to user
            self.state_manager.add_success_message("Progress log copied to clipboard!")

        except Exception as ex:
            self.state_manager.add_error_message(f"Failed to copy log: {str(ex)}")

    def _add_log_message(self, message: str, color: str = IPAColors.CHARCOAL):
        """Add a message to the progress log."""
        timestamp = time.strftime("%H:%M:%S")

        # Store message with timestamp for copying
        log_message_text = f"[{timestamp}] {message}"
        self.progress_messages.append(log_message_text)

        # Keep only last 50 messages to prevent memory issues
        if len(self.progress_messages) > 50:
            self.progress_messages.pop(0)

        log_entry = ft.Row(
            [
                ft.Text(
                    f"[{timestamp}]",
                    size=IPATypography.BODY_SMALL,
                    color=IPAColors.DARK_GREY,
                    font_family="Consolas, monospace",
                ),
                ft.Text(
                    message,
                    size=IPATypography.BODY_SMALL,
                    color=color,
                    expand=True,
                    selectable=True,  # Make text selectable for manual copying
                ),
            ]
        )

        if self.progress_log:
            self.progress_log.controls.append(log_entry)
            # Keep only last 20 UI entries to prevent memory issues
            if len(self.progress_log.controls) > 20:
                self.progress_log.controls.pop(0)
            with contextlib.suppress(Exception):
                # Ignore if page is no longer available
                self.page.update()

    def _update_progress(self, progress: float, task_description: str):
        """Update the progress bar and current task."""
        if self.overall_progress_bar:
            self.overall_progress_bar.value = progress

        if self.current_task_text:
            self.current_task_text.value = task_description

        if self.progress_percentage_text:
            self.progress_percentage_text.value = f"{int(progress * 100)}%"

        # Safe page update
        with contextlib.suppress(Exception):
            # Ignore if page is no longer available
            self.page.update()

    def _update_current_task(self, task: str):
        """Update just the current task text."""
        if self.current_task_text:
            self.current_task_text.value = task
            with contextlib.suppress(Exception):
                # Ignore if page is no longer available
                self.page.update()

    def start_analysis(self):
        """Start the PII detection analysis."""
        # print("DEBUG: start_analysis() called")
        if not self.is_analysis_running:
            # print("DEBUG: Analysis is not running, starting new analysis")
            self.is_analysis_running = True
            self.analysis_cancelled = False
            self.analysis_complete = False

            # Update UI only if components exist
            if self.cancel_button:
                self.cancel_button.disabled = False
            if self.view_results_button:
                self.view_results_button.disabled = True

            self._add_log_message(
                "Starting PII detection analysis...", IPAColors.IPA_GREEN
            )

            # Load datasets first
            self._load_datasets_and_start_analysis()

    def _load_datasets_and_start_analysis(self):
        """Load datasets and start real PII analysis."""
        # print("DEBUG: _load_datasets_and_start_analysis() called")

        def load_and_analyze():
            # print("DEBUG: load_and_analyze() thread started")
            try:
                # Step 1: Load datasets
                self._update_progress(0.1, "Loading dataset files...")
                self._add_log_message("Loading dataset files...")

                files = self.state_manager.state.selected_files
                if not files:
                    self._add_log_message(
                        "No files selected for analysis", IPAColors.ERROR
                    )
                    self._update_current_task("Analysis failed - no files selected")
                    self.is_analysis_running = False
                    if self.cancel_button:
                        self.cancel_button.disabled = True
                    return

                # For now, process first file (could be extended for multiple files)
                first_file = files[0]
                success, message = self.adapter.load_dataset(str(first_file.path))

                if not success:
                    self._add_log_message(
                        f"Failed to load dataset: {message}", IPAColors.ERROR
                    )
                    self._update_current_task("Dataset loading failed")
                    self.is_analysis_running = False
                    return

                self._add_log_message(message, IPAColors.SUCCESS)
                self._update_progress(0.2, "Dataset loaded successfully")

                # Step 2: Start real PII analysis
                self._start_real_pii_analysis()

            except Exception as e:
                self._add_log_message(
                    f"Error during dataset loading: {str(e)}", IPAColors.ERROR
                )
                self._update_current_task("Analysis failed")
                self.is_analysis_running = False

        threading.Thread(target=load_and_analyze, daemon=True).start()

    def _start_real_pii_analysis(self):
        """Start the real PII detection analysis using the backend."""
        try:

            def progress_callback(progress: float, message: str):
                """Handle progress updates from backend."""
                if not self.analysis_cancelled:
                    self._update_progress(0.2 + (0.7 * progress), message)
                    self._add_log_message(message)

            def completion_callback(success: bool, results):
                """Handle analysis completion."""
                if self.analysis_cancelled:
                    return

                if success:
                    # Store results in state
                    self.state_manager.state.detection_results = results

                    # Initialize smart default anonymization methods for each column
                    self._initialize_default_anonymization_methods(results)

                    # Update UI
                    self.analysis_complete = True
                    self.is_analysis_running = False

                    self._update_progress(1.0, "Analysis completed successfully!")
                    self._add_log_message(
                        f"Analysis completed! Found {len(results)} potentially sensitive columns.",
                        IPAColors.SUCCESS,
                    )

                    # Enable results button
                    if self.view_results_button:
                        self.view_results_button.disabled = False
                    if self.cancel_button:
                        self.cancel_button.disabled = True

                    # Show completion notification
                    try:
                        self.page.update()
                        self._show_completion_notification()
                    except Exception:
                        pass
                else:
                    self._add_log_message("Analysis failed", IPAColors.ERROR)
                    self._update_current_task("Analysis failed")
                    self.is_analysis_running = False

            # Start background processing
            self.background_processor.run_analysis_async(
                self.state_manager.state.detection_config,
                self.state_manager.state.geonames_api_key,
                progress_callback,
                completion_callback,
            )

        except Exception as e:
            self._add_log_message(f"Error starting analysis: {str(e)}", IPAColors.ERROR)
            self._update_current_task("Analysis failed")
            self.is_analysis_running = False

    def _handle_cancellation_cleanup(self):
        """Handle cleanup after analysis cancellation."""
        time.sleep(1)  # Brief delay to simulate cleanup

        self.is_analysis_running = False
        self.analysis_cancelled = True

        self._update_current_task("Analysis cancelled")
        self._add_log_message("Analysis cancelled successfully", IPAColors.WARNING)

        # Re-enable back button, keep cancel disabled
        with contextlib.suppress(Exception):
            # Ignore if page is no longer available
            self.page.update()

    def _show_completion_notification(self):
        """Show analysis completion notification."""

        def close_dialog(e):
            dialog.open = False
            self.page.update()

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Analysis Complete!", color=IPAColors.SUCCESS),
            content=ft.Column(
                [
                    ft.Icon(ft.Icons.CHECK_CIRCLE, color=IPAColors.SUCCESS, size=48),
                    ft.Text(
                        "Your dataset has been successfully analyzed for PII. The anonymized version is ready for review.",
                        text_align=ft.TextAlign.CENTER,
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                tight=True,
            ),
            actions=[
                ft.TextButton(
                    "View Results",
                    on_click=lambda e: (close_dialog(e), self._handle_view_results(e)),
                ),
                ft.TextButton("Close", on_click=close_dialog),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        self.page.open(dialog)

    def on_state_changed(self, state: AppState):
        """Handle state changes."""
        # Only start analysis when we actually navigate TO the progress screen
        if (
            state.current_screen == AppConstants.SCREEN_PROGRESS
            and not self.is_analysis_running
            and not self.analysis_complete
        ):
            # Small delay to ensure UI is fully loaded
            threading.Timer(0.5, self.start_analysis).start()

    def on_screen_enter(self):
        """Enter this screen and reset analysis state."""
        # Reset analysis state for new analysis
        self.is_analysis_running = False
        self.analysis_cancelled = False
        self.analysis_complete = False

        if self.overall_progress_bar:
            self.overall_progress_bar.value = 0

        if self.current_task_text:
            self.current_task_text.value = "Preparing analysis..."

        if self.progress_percentage_text:
            self.progress_percentage_text.value = "0%"

        if self.progress_log:
            self.progress_log.controls.clear()
            self.progress_log.controls.append(
                ft.Text(
                    "Ready to start analysis",
                    size=IPATypography.BODY_SMALL,
                    color=IPAColors.DARK_GREY,
                )
            )

        # Reset progress messages for copying
        self.progress_messages = ["Ready to start analysis"]

    def _initialize_default_anonymization_methods(self, results):
        """Initialize smart default anonymization methods for detected PII columns.

        Args:
            results: List of DetectionResult objects from analysis

        """
        default_methods = {}

        for result in results:
            column_lower = result.column.lower()
            pii_type_lower = result.pii_type.lower()

            # Smart defaults based on confidence, column name, and PII type
            if result.confidence > 0.8:
                # High confidence = high risk, default to remove
                default_methods[result.column] = "remove"
            elif any(
                keyword in pii_type_lower
                for keyword in ["email", "phone", "ssn", "credit"]
            ):
                # Sensitive patterns should be masked
                default_methods[result.column] = "mask"
            elif any(
                keyword in column_lower
                for keyword in ["age", "date", "year", "time", "dob", "birth"]
            ):
                # Date/age columns are good candidates for categorization
                default_methods[result.column] = "categorize"
            elif any(
                keyword in column_lower
                for keyword in ["location", "address", "city", "state", "zip"]
            ):
                # Location columns can be generalized/categorized
                default_methods[result.column] = "categorize"
            elif any(
                keyword in column_lower
                for keyword in ["income", "salary", "wage", "earnings"]
            ):
                # Financial data can be categorized into ranges
                default_methods[result.column] = "categorize"
            else:
                # Default to encoding for everything else
                default_methods[result.column] = "encode"

        # Update state with default methods
        self.state_manager.state.column_anonymization_methods = default_methods

        self._add_log_message(
            f"Initialized anonymization defaults for {len(default_methods)} columns (can be customized in Results)",
            IPAColors.INFO,
        )
