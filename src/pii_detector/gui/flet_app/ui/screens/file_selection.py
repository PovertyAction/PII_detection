"""File selection screen for choosing dataset files."""

from pathlib import Path

import flet as ft

from pii_detector.gui.flet_app.config.constants import (
    AppConstants,
    IPAColors,
    IPASpacing,
    IPATypography,
)
from pii_detector.gui.flet_app.config.settings import (
    AppState,
    FileInfo,
    ValidationResult,
)
from pii_detector.gui.flet_app.ui.components.buttons import (
    create_primary_button,
    create_secondary_button,
)


class FileSelectionScreen:
    """File selection screen implementation."""

    def __init__(self, page: ft.Page, state_manager):
        """Initialize the file selection screen.

        Args:
            page: Flet page instance
            state_manager: Application state manager

        """
        self.page = page
        self.state_manager = state_manager
        self._screen_name = AppConstants.SCREEN_FILE_SELECTION

        # File picker
        self.file_picker = ft.FilePicker(on_result=self._handle_file_picker_result)

        # Add file picker to page overlay if not already added
        if self.file_picker not in self.page.overlay:
            self.page.overlay.append(self.file_picker)

        # UI components that need updating
        self.file_list_container = None
        self.next_button = None
        self.drop_zone = None

    def build(self) -> ft.Container:
        """Build the file selection screen."""
        container = ft.Container(
            content=ft.Column(
                [
                    # Title and description
                    self._build_header(),
                    # User feedback messages
                    self._build_messages(),
                    # File drop zone
                    self._build_drop_zone(),
                    # Selected files list
                    self._build_selected_files_section(),
                    # Action buttons
                    self._build_action_buttons(),
                ],
                spacing=IPASpacing.LG,
                scroll=ft.ScrollMode.AUTO,
            ),
            padding=IPASpacing.XL,
            expand=True,
        )

        # Update file list display now that UI components are built
        self._update_file_list_display()

        return container

    def _build_messages(self) -> ft.Container:
        """Build user feedback messages."""
        messages = []

        # Error messages
        for error in self.state_manager.state.error_messages:
            messages.append(
                ft.Container(
                    content=ft.Row(
                        [
                            ft.Icon(ft.Icons.ERROR, color=IPAColors.ERROR, size=16),
                            ft.Text(
                                error,
                                color=IPAColors.ERROR,
                                size=IPATypography.BODY_SMALL,
                            ),
                        ]
                    ),
                    padding=IPASpacing.SM,
                    bgcolor=IPAColors.ERROR + "20",  # 20% opacity
                    border_radius=IPASpacing.RADIUS_SM,
                )
            )

        # Success messages
        for success in self.state_manager.state.success_messages:
            messages.append(
                ft.Container(
                    content=ft.Row(
                        [
                            ft.Icon(
                                ft.Icons.CHECK_CIRCLE, color=IPAColors.SUCCESS, size=16
                            ),
                            ft.Text(
                                success,
                                color=IPAColors.SUCCESS,
                                size=IPATypography.BODY_SMALL,
                            ),
                        ]
                    ),
                    padding=IPASpacing.SM,
                    bgcolor=IPAColors.SUCCESS + "20",  # 20% opacity
                    border_radius=IPASpacing.RADIUS_SM,
                )
            )

        return ft.Container(
            content=ft.Column(messages, spacing=IPASpacing.XS),
            visible=len(messages) > 0,
        )

    def _build_header(self) -> ft.Column:
        """Build the screen header."""
        return ft.Column(
            [
                ft.Text(
                    "Select Dataset Files",
                    size=IPATypography.HEADER_2,
                    weight=ft.FontWeight.W_600,
                    color=IPAColors.DARK_BLUE,
                ),
                ft.Text(
                    "Choose the dataset files you want to analyze for PII. You can select single or multiple files.",
                    size=IPATypography.BODY_REGULAR,
                    color=IPAColors.CHARCOAL,
                ),
            ],
            spacing=IPASpacing.SM,
        )

    def _build_drop_zone(self) -> ft.Container:
        """Build the file selection zone."""
        self.drop_zone = ft.Container(
            content=ft.Column(
                [
                    ft.Icon(
                        ft.Icons.FOLDER_OPEN,
                        size=48,
                        color=IPAColors.IPA_GREEN,
                    ),
                    ft.Text(
                        "Click to browse files",
                        size=IPATypography.HEADER_3,
                        weight=ft.FontWeight.W_500,
                        color=IPAColors.CHARCOAL,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    ft.Text(
                        f"Supports: {', '.join(AppConstants.SUPPORTED_FORMATS)} (max {AppConstants.MAX_FILE_SIZE_MB}MB each)",
                        size=IPATypography.BODY_SMALL,
                        color=IPAColors.DARK_GREY,
                        text_align=ft.TextAlign.CENTER,
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=IPASpacing.SM,
            ),
            height=200,
            padding=IPASpacing.XL,
            border=ft.border.all(3, IPAColors.DARK_GREY),
            border_radius=IPASpacing.RADIUS_LG,
            bgcolor=IPAColors.LIGHT_GREY,
            alignment=ft.alignment.center,
            on_click=self._handle_browse_click,
        )

        return self.drop_zone

    def _build_selected_files_section(self) -> ft.Column:
        """Build the selected files section."""
        # Create the container that will hold the file list
        self.file_list_container = ft.Container(
            content=ft.Text(
                "No files selected",
                size=IPATypography.BODY_REGULAR,
                color=IPAColors.DARK_GREY,
                text_align=ft.TextAlign.CENTER,
            ),
            padding=IPASpacing.MD,
            border=ft.border.all(1, IPAColors.DARK_GREY),
            border_radius=IPASpacing.RADIUS_MD,
            bgcolor=IPAColors.WHITE,
            alignment=ft.alignment.center,
        )

        return ft.Column(
            [
                ft.Text(
                    "Selected Files:",
                    size=IPATypography.BODY_LARGE,
                    weight=ft.FontWeight.W_600,
                    color=IPAColors.CHARCOAL,
                ),
                self.file_list_container,
            ],
            spacing=IPASpacing.SM,
        )

    def _build_action_buttons(self) -> ft.Column:
        """Build the action buttons."""
        self.next_button = create_primary_button(
            text="Next: Configure Analysis",
            on_click=self._handle_next_click,
            icon=ft.Icons.ARROW_FORWARD,
            disabled=len(self.state_manager.state.selected_files) == 0,
        )

        return ft.Column(
            [
                # Demo data button
                ft.Row(
                    [
                        create_secondary_button(
                            text="Load Demo Data",
                            on_click=self._handle_load_demo,
                            icon=ft.Icons.DATASET,
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                ),
                # Main action buttons
                ft.Row(
                    [
                        create_secondary_button(
                            text="Clear All",
                            on_click=self._handle_clear_all,
                            icon=ft.Icons.CLEAR,
                            disabled=len(self.state_manager.state.selected_files) == 0,
                        ),
                        create_secondary_button(
                            text="Add More Files",
                            on_click=self._handle_browse_click,
                            icon=ft.Icons.ADD,
                        ),
                        self.next_button,
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
            ],
            spacing=IPASpacing.SM,
        )

    def _handle_browse_click(self, e):
        """Handle browse button click."""
        self.file_picker.pick_files(
            dialog_title="Select dataset files",
            file_type=ft.FilePickerFileType.CUSTOM,
            allowed_extensions=["csv", "xlsx", "xls", "dta"],
            allow_multiple=True,
        )

    def _handle_file_picker_result(self, e: ft.FilePickerResultEvent):
        """Handle file picker result."""
        if e.files:
            new_files = []
            for file in e.files:
                file_info = self._create_file_info(Path(file.path))
                validation_result = self._validate_file(file_info)

                new_files.append(file_info)
                self.state_manager.state.file_validation_results[file.path] = (
                    validation_result
                )

            # Add to selected files (avoiding duplicates)
            existing_paths = {f.path for f in self.state_manager.state.selected_files}
            filtered_new_files = [f for f in new_files if f.path not in existing_paths]

            if filtered_new_files:
                updated_files = (
                    self.state_manager.state.selected_files + filtered_new_files
                )
                self.state_manager.update_state(selected_files=updated_files)

                # Show success message
                self.state_manager.add_success_message(
                    f"Added {len(filtered_new_files)} file(s) to selection"
                )
            else:
                self.state_manager.add_error_message(
                    "All selected files are already in the list"
                )

    def _create_file_info(self, file_path: Path) -> FileInfo:
        """Create FileInfo object from path."""
        try:
            size_mb = file_path.stat().st_size / (1024 * 1024)  # Convert to MB
            return FileInfo(
                path=file_path,
                name=file_path.name,
                size_mb=round(size_mb, 2),
                format=file_path.suffix.lower(),
                is_valid=True,
            )
        except Exception as e:
            return FileInfo(
                path=file_path,
                name=file_path.name,
                size_mb=0,
                format=file_path.suffix.lower(),
                is_valid=False,
                validation_message=f"Error reading file: {str(e)}",
            )

    def _validate_file(self, file_info: FileInfo) -> ValidationResult:
        """Validate a selected file."""
        # Check file format
        if file_info.format not in AppConstants.SUPPORTED_FORMATS:
            return ValidationResult(
                is_valid=False,
                message=f"Unsupported format: {file_info.format}",
                details={"supported_formats": AppConstants.SUPPORTED_FORMATS},
            )

        # Check file size
        if file_info.size_mb > AppConstants.MAX_FILE_SIZE_MB:
            return ValidationResult(
                is_valid=False,
                message=f"File too large: {file_info.size_mb}MB (max: {AppConstants.MAX_FILE_SIZE_MB}MB)",
                details={"max_size_mb": AppConstants.MAX_FILE_SIZE_MB},
            )

        # Check if file exists and is readable
        if not file_info.path.exists():
            return ValidationResult(
                is_valid=False,
                message="File does not exist",
            )

        if not file_info.path.is_file():
            return ValidationResult(
                is_valid=False,
                message="Path is not a file",
            )

        return ValidationResult(
            is_valid=True,
            message="File is valid",
        )

    def _update_file_list_display(self):
        """Update the file list display."""
        # Only update if the UI components have been built
        if not self.file_list_container or not self.next_button:
            return

        files = self.state_manager.state.selected_files

        if not files:
            # Double check that container still exists
            if self.file_list_container:
                self.file_list_container.content = ft.Text(
                    "No files selected",
                    size=IPATypography.BODY_REGULAR,
                    color=IPAColors.DARK_GREY,
                    text_align=ft.TextAlign.CENTER,
                )
                self.file_list_container.alignment = ft.alignment.center
        else:
            # Create file list items
            file_items = []
            for i, file_info in enumerate(files):
                validation = self.state_manager.state.file_validation_results.get(
                    str(file_info.path),
                    ValidationResult(is_valid=True, message="Valid"),
                )

                # Status icon and color
                if validation.is_valid:
                    status_icon = ft.Icons.CHECK_CIRCLE
                    status_color = IPAColors.SUCCESS
                    status_text = "Valid"
                else:
                    status_icon = ft.Icons.ERROR
                    status_color = IPAColors.ERROR
                    status_text = validation.message

                file_item = ft.Container(
                    content=ft.Row(
                        [
                            ft.Icon(
                                status_icon,
                                size=20,
                                color=status_color,
                            ),
                            ft.Column(
                                [
                                    ft.Text(
                                        file_info.name,
                                        size=IPATypography.BODY_REGULAR,
                                        weight=ft.FontWeight.W_500,
                                        color=IPAColors.CHARCOAL,
                                    ),
                                    ft.Text(
                                        f"{file_info.size_mb}MB • {file_info.format.upper()} • {status_text}",
                                        size=IPATypography.BODY_SMALL,
                                        color=IPAColors.DARK_GREY
                                        if validation.is_valid
                                        else status_color,
                                    ),
                                ],
                                expand=True,
                                spacing=2,
                            ),
                            ft.IconButton(
                                icon=ft.Icons.CLOSE,
                                tooltip="Remove file",
                                icon_color=IPAColors.RED_ORANGE,
                                on_click=lambda e, idx=i: self._remove_file(idx),
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    padding=ft.padding.symmetric(
                        horizontal=IPASpacing.SM, vertical=IPASpacing.XS
                    ),
                    border=ft.border.only(bottom=ft.BorderSide(1, IPAColors.LIGHT_GREY))
                    if i < len(files) - 1
                    else None,
                )

                file_items.append(file_item)

            if self.file_list_container:
                self.file_list_container.content = ft.Column(
                    file_items,
                    spacing=0,
                    tight=True,
                )
                self.file_list_container.alignment = None

        # Update next button state
        if self.next_button:
            valid_files = [
                f
                for f in files
                if self.state_manager.state.file_validation_results.get(
                    str(f.path), ValidationResult(is_valid=True, message="Valid")
                ).is_valid
            ]
            self.next_button.disabled = len(valid_files) == 0

        self.page.update()

    def _remove_file(self, index: int):
        """Remove a file from the selection."""
        files = self.state_manager.state.selected_files.copy()
        if 0 <= index < len(files):
            removed_file = files.pop(index)
            # Also remove from validation results
            validation_results = self.state_manager.state.file_validation_results.copy()
            validation_results.pop(str(removed_file.path), None)

            self.state_manager.update_state(
                selected_files=files, file_validation_results=validation_results
            )

    def _handle_load_demo(self, e):
        """Load demo data for testing."""
        demo_file_path = Path("src/pii_detector/data/demo_data.csv")

        if demo_file_path.exists():
            file_info = self._create_file_info(demo_file_path)
            validation_result = self._validate_file(file_info)

            # Replace current selection with demo data
            self.state_manager.update_state(
                selected_files=[file_info],
                file_validation_results={str(demo_file_path): validation_result},
            )

            self.state_manager.add_success_message("Demo data loaded successfully!")
        else:
            self.state_manager.add_error_message(
                "Demo data file not found. Please use 'Add More Files' to select your own dataset."
            )

    def _handle_clear_all(self, e):
        """Handle clear all button click."""
        self.state_manager.update_state(selected_files=[], file_validation_results={})

    def _handle_next_click(self, e):
        """Handle next button click."""
        # Validate that we have at least one valid file
        valid_files = []
        for file_info in self.state_manager.state.selected_files:
            validation = self.state_manager.state.file_validation_results.get(
                str(file_info.path), ValidationResult(is_valid=True, message="Valid")
            )
            if validation.is_valid:
                valid_files.append(file_info)

        if not valid_files:
            self.state_manager.add_error_message(
                "Please select at least one valid file"
            )
            return

        # Navigate to configuration screen
        self.state_manager.navigate_to(AppConstants.SCREEN_CONFIGURATION)

    def on_state_changed(self, state: AppState):
        """Handle state changes."""
        # Update file list display when selected files change, but only if components are initialized
        if self.file_list_container is not None and self.next_button is not None:
            self._update_file_list_display()

        # Clear messages after a few seconds (auto-dismiss)
        if state.success_messages or state.error_messages:
            # Auto-clear messages after 3 seconds
            import threading

            def clear_messages():
                try:
                    import time

                    time.sleep(3)
                    # Only clear if we're still on this screen and the app is running
                    if (
                        hasattr(self.state_manager, "state")
                        and self.state_manager.state.current_screen
                        == AppConstants.SCREEN_FILE_SELECTION
                    ):
                        self.state_manager.clear_messages()
                except Exception:
                    # Ignore errors if app is shutting down or screen changed
                    pass

            threading.Timer(3.0, clear_messages).start()
