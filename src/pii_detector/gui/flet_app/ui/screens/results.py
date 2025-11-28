"""Results screen for displaying PII detection results."""

import time
from pathlib import Path

import flet as ft

from pii_detector.gui.flet_app.backend_adapter import PIIDetectionAdapter
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
from pii_detector.gui.flet_app.ui.components.cards import create_metric_card


class ResultsScreen:
    """Results screen implementation (placeholder)."""

    def __init__(self, page: ft.Page, state_manager):
        """Initialize the results screen.

        Args:
            page: Flet page instance
            state_manager: Application state manager

        """
        self.page = page
        self.state_manager = state_manager
        self._screen_name = AppConstants.SCREEN_RESULTS

        # Create adapter instance to access dataset
        self.adapter = PIIDetectionAdapter()

        # Track dropdowns for each column
        self.column_method_dropdowns = {}

    def build(self) -> ft.Container:
        """Build the results screen."""
        return ft.Container(
            content=ft.Column(
                [
                    # Title
                    ft.Text(
                        "PII Detection Results",
                        size=IPATypography.HEADER_2,
                        weight=ft.FontWeight.W_600,
                        color=IPAColors.DARK_BLUE,
                    ),
                    # Summary metrics
                    self._build_summary_metrics(),
                    # Results table
                    self._build_results_table(),
                    # Action buttons
                    ft.Row(
                        [
                            create_secondary_button(
                                text="New Analysis",
                                on_click=lambda e: self.state_manager.navigate_to(
                                    AppConstants.SCREEN_DASHBOARD
                                ),
                                icon=ft.Icons.ADD,
                            ),
                            create_secondary_button(
                                text="Preview Data",
                                on_click=self._handle_preview_data,
                                icon=ft.Icons.VISIBILITY,
                            ),
                            create_secondary_button(
                                text="Generate PII Report",
                                on_click=self._handle_generate_export,
                                icon=ft.Icons.FILE_DOWNLOAD,
                            ),
                            create_primary_button(
                                text="Export Deidentified Data",
                                on_click=self._handle_download_deidentified,
                                icon=ft.Icons.DOWNLOAD,
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

    def _build_summary_metrics(self) -> ft.Row:
        """Build the summary metrics cards."""
        # Get detection results from state
        results = self.state_manager.state.detection_results

        # Calculate metrics
        total_pii = len(results)
        high_conf = sum(1 for r in results if r.confidence > 0.8)
        medium_conf = sum(1 for r in results if 0.5 <= r.confidence <= 0.8)
        low_conf = sum(1 for r in results if r.confidence < 0.5)

        return ft.Row(
            [
                create_metric_card(
                    title="PII Detected",
                    value=str(total_pii),
                    subtitle="Columns",
                    color=IPAColors.RED_ORANGE,
                    icon=ft.Icons.WARNING,
                ),
                create_metric_card(
                    title="High Confidence",
                    value=str(high_conf),
                    subtitle="> 0.8 score",
                    color=IPAColors.HIGH_CONFIDENCE,
                    icon=ft.Icons.SECURITY,
                ),
                create_metric_card(
                    title="Medium Confidence",
                    value=str(medium_conf),
                    subtitle="0.5-0.8 score",
                    color=IPAColors.MED_CONFIDENCE,
                    icon=ft.Icons.INFO,
                ),
                create_metric_card(
                    title="Low Confidence",
                    value=str(low_conf),
                    subtitle="< 0.5 score",
                    color=IPAColors.DARK_GREY,
                    icon=ft.Icons.HELP,
                ),
            ],
            alignment=ft.MainAxisAlignment.SPACE_EVENLY,
        )

    def _build_results_table(self) -> ft.Container:
        """Build the results table showing detected PII columns."""
        results = self.state_manager.state.detection_results

        if not results:
            # Show message if no results
            return ft.Container(
                content=ft.Column(
                    [
                        ft.Icon(
                            ft.Icons.CHECK_CIRCLE, size=64, color=IPAColors.SUCCESS
                        ),
                        ft.Text(
                            "No PII Detected",
                            size=IPATypography.HEADER_3,
                            color=IPAColors.CHARCOAL,
                        ),
                        ft.Text(
                            "No personally identifiable information was found in the dataset.",
                            size=IPATypography.BODY_REGULAR,
                            color=IPAColors.DARK_GREY,
                        ),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=IPASpacing.MD,
                ),
                padding=IPASpacing.XL,
                alignment=ft.alignment.center,
            )

        # Create table rows
        rows = []
        for result in results:
            # Color code confidence
            if result.confidence > 0.8:
                conf_color = IPAColors.HIGH_CONFIDENCE
            elif result.confidence >= 0.5:
                conf_color = IPAColors.MED_CONFIDENCE
            else:
                conf_color = IPAColors.DARK_GREY

            # Get current anonymization method for this column
            current_method = self.state_manager.state.column_anonymization_methods.get(
                result.column, "remove"
            )

            # Create dropdown for anonymization method selection
            method_dropdown = ft.Dropdown(
                value=current_method,
                options=[
                    ft.dropdown.Option("unchanged", "Unchanged"),
                    ft.dropdown.Option("remove", "Remove"),
                    ft.dropdown.Option("encode", "Encode"),
                    ft.dropdown.Option("categorize", "Categorize"),
                    ft.dropdown.Option("mask", "Mask"),
                ],
                width=150,
                dense=True,
                text_size=IPATypography.BODY_SMALL,
                content_padding=ft.padding.symmetric(horizontal=8, vertical=4),
                on_change=lambda e, col=result.column: self._on_method_change(
                    col, e.control.value
                ),
            )

            # Store reference to dropdown
            self.column_method_dropdowns[result.column] = method_dropdown

            row = ft.DataRow(
                cells=[
                    ft.DataCell(
                        ft.Text(
                            result.column,
                            weight=ft.FontWeight.W_600,
                            color=IPAColors.CHARCOAL,
                        )
                    ),
                    ft.DataCell(ft.Text(result.method, color=IPAColors.CHARCOAL)),
                    ft.DataCell(
                        ft.Container(
                            content=ft.Text(
                                f"{result.confidence:.2f}",
                                color="white",
                                size=IPATypography.BODY_SMALL,
                                weight=ft.FontWeight.W_600,
                            ),
                            bgcolor=conf_color,
                            padding=ft.padding.symmetric(horizontal=8, vertical=4),
                            border_radius=4,
                        )
                    ),
                    ft.DataCell(ft.Text(result.pii_type, color=IPAColors.CHARCOAL)),
                    ft.DataCell(method_dropdown),  # New column with dropdown
                ],
            )
            rows.append(row)

        # Create data table
        table = ft.DataTable(
            columns=[
                ft.DataColumn(
                    ft.Text(
                        "Column", weight=ft.FontWeight.W_600, color=IPAColors.DARK_BLUE
                    )
                ),
                ft.DataColumn(
                    ft.Text(
                        "Method", weight=ft.FontWeight.W_600, color=IPAColors.DARK_BLUE
                    )
                ),
                ft.DataColumn(
                    ft.Text(
                        "Confidence",
                        weight=ft.FontWeight.W_600,
                        color=IPAColors.DARK_BLUE,
                    )
                ),
                ft.DataColumn(
                    ft.Text(
                        "PII Type",
                        weight=ft.FontWeight.W_600,
                        color=IPAColors.DARK_BLUE,
                    )
                ),
                ft.DataColumn(
                    ft.Text(
                        "Anonymization",
                        weight=ft.FontWeight.W_600,
                        color=IPAColors.DARK_BLUE,
                    )
                ),
            ],
            rows=rows,
            border=ft.border.all(1, IPAColors.DARK_GREY),
            border_radius=IPASpacing.RADIUS_MD,
            horizontal_lines=ft.BorderSide(1, IPAColors.LIGHT_GREY),
            heading_row_color=IPAColors.BLUE_ACCENT,
        )

        return ft.Container(
            content=ft.Column(
                [
                    ft.Text(
                        "Detected PII Columns",
                        size=IPATypography.BODY_LARGE,
                        weight=ft.FontWeight.W_600,
                        color=IPAColors.CHARCOAL,
                    ),
                    # Helper text
                    ft.Container(
                        content=ft.Row(
                            [
                                ft.Icon(
                                    ft.Icons.INFO_OUTLINE,
                                    color=IPAColors.DARK_BLUE,
                                    size=16,
                                ),
                                ft.Text(
                                    "Select how to handle each PII column when exporting deidentified data. Smart defaults have been applied based on detection confidence and column type. Choose 'Unchanged' to preserve columns you disagree with the detection.",
                                    size=IPATypography.BODY_SMALL,
                                    color=IPAColors.DARK_GREY,
                                ),
                            ],
                            spacing=IPASpacing.XS,
                        ),
                        padding=IPASpacing.SM,
                        bgcolor=IPAColors.BLUE_ACCENT,
                        border_radius=IPASpacing.RADIUS_SM,
                    ),
                    ft.Container(
                        content=table,
                        bgcolor=IPAColors.WHITE,
                        border_radius=IPASpacing.RADIUS_MD,
                    ),
                ],
                spacing=IPASpacing.SM,
            ),
            padding=IPASpacing.MD,
        )

    def _on_method_change(self, column: str, method: str):
        """Handle anonymization method change for a column.

        Args:
            column: Name of the column
            method: Selected anonymization method (remove/encode/categorize/mask)

        """
        # Update state with new method
        current_methods = self.state_manager.state.column_anonymization_methods.copy()
        current_methods[column] = method
        self.state_manager.state.column_anonymization_methods = current_methods

    def _handle_preview_data(self, e):
        """Handle preview data button click."""
        # print("DEBUG: Preview Data button clicked")

        # Get the selected file information
        files = self.state_manager.state.selected_files
        results = self.state_manager.state.detection_results

        if not files:
            # print("DEBUG: No files found, showing dialog")
            self._show_dialog("No Data", "No dataset file is currently loaded.")
            return

        file_info = files[0]

        # Load dataset to preview
        try:
            import pandas as pd

            # Determine file type and load accordingly
            file_path = str(file_info.path)

            if file_path.endswith(".csv"):
                # print("DEBUG: Loading as CSV")
                df = pd.read_csv(file_path)
            elif file_path.endswith(".xlsx"):
                # print("DEBUG: Loading as Excel")
                df = pd.read_excel(file_path)
            elif file_path.endswith(".dta"):
                # print("DEBUG: Loading as Stata")
                df = pd.read_stata(file_path)
            else:
                self._show_dialog(
                    "Unsupported Format",
                    f"Unable to preview this file format: {file_path}",
                )
                return

            # Get first 5 rows
            preview_df = df.head(5)

            # Create preview dialog
            self._show_data_preview_dialog(preview_df, results)

        except Exception as ex:
            import traceback

            traceback.print_exc()
            self._show_dialog(
                "Preview Error",
                f"Failed to load data preview:\n\n{type(ex).__name__}: {str(ex)}",
            )

    def _show_data_preview_dialog(self, df, results):
        """Show data preview dialog with PII columns highlighted."""

        def close_dialog(e):
            dialog.open = False
            self.page.update()

        # Get list of PII column names
        pii_columns = [r.column for r in results]

        # Create table headers
        headers = []
        for col in df.columns:
            is_pii = col in pii_columns
            headers.append(
                ft.DataColumn(
                    ft.Container(
                        content=ft.Text(
                            col,
                            weight=ft.FontWeight.W_600,
                            color="white" if is_pii else IPAColors.DARK_BLUE,
                            size=IPATypography.BODY_SMALL,
                        ),
                        bgcolor=IPAColors.RED_ORANGE if is_pii else None,
                        padding=4,
                        border_radius=4,
                    )
                )
            )

        # Create table rows
        rows = []
        for idx, row in df.iterrows():
            cells = []
            for col in df.columns:
                is_pii = col in pii_columns
                value = str(row[col])
                # Truncate long values
                if len(value) > 30:
                    value = value[:27] + "..."

                cells.append(
                    ft.DataCell(
                        ft.Container(
                            content=ft.Text(
                                value,
                                size=IPATypography.BODY_SMALL,
                                color=IPAColors.RED_ORANGE
                                if is_pii
                                else IPAColors.CHARCOAL,
                                weight=ft.FontWeight.W_600
                                if is_pii
                                else ft.FontWeight.NORMAL,
                            ),
                            bgcolor=IPAColors.BLUE_ACCENT if is_pii else None,
                            padding=4,
                            border_radius=4,
                        )
                    )
                )
            rows.append(ft.DataRow(cells=cells))

        preview_table = ft.DataTable(
            columns=headers,
            rows=rows,
            border=ft.border.all(1, IPAColors.DARK_GREY),
            horizontal_lines=ft.BorderSide(1, IPAColors.LIGHT_GREY),
        )

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Data Preview (First 5 Rows)"),
            content=ft.Container(
                content=ft.Column(
                    [
                        ft.Container(
                            content=ft.Row(
                                [
                                    ft.Icon(
                                        ft.Icons.WARNING,
                                        color=IPAColors.RED_ORANGE,
                                        size=16,
                                    ),
                                    ft.Text(
                                        "PII columns are highlighted in orange",
                                        size=IPATypography.BODY_SMALL,
                                        color=IPAColors.DARK_GREY,
                                    ),
                                ],
                                spacing=8,
                            ),
                            bgcolor=IPAColors.BLUE_ACCENT,
                            padding=8,
                            border_radius=4,
                        ),
                        # ft.Container(
                        #    content=preview_table,
                        #    width=800,
                        # ),
                        # ),
                        ft.Container(
                            content=ft.Row(
                                controls=[preview_table],
                                scroll=ft.ScrollMode.AUTO,  # I added this to enable horizontal scroll
                            ),
                            width=800,
                        ),
                    ],
                    spacing=IPASpacing.SM,
                    scroll=ft.ScrollMode.AUTO,
                ),
                height=400,
            ),
            actions=[
                ft.TextButton("Close", on_click=close_dialog),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        # print("DEBUG: Opening dialog using page.open()")
        self.page.open(dialog)
        # print("DEBUG: Preview dialog opened")

    def _handle_download_deidentified(self, e):
        """Handle download deidentified data button click."""

        # Use file picker to select save location
        def handle_save_result(e: ft.FilePickerResultEvent):
            if e.path:
                save_path = Path(e.path)
                self._perform_anonymization_and_save(save_path)

        file_picker = ft.FilePicker(on_result=handle_save_result)
        self.page.overlay.append(file_picker)
        self.page.update()

        # Determine default filename from original file
        files = self.state_manager.state.selected_files
        if files:
            original_name = files[0].name
            original_ext = files[0].format

            # Remove the extension from the filename using Path
            from pathlib import Path

            path_obj = Path(original_name)
            base_name = path_obj.stem  # Gets filename without extension

            # Create new filename with _deidentified suffix
            if original_ext:
                default_name = f"{base_name}_deidentified.{original_ext}"
            else:
                # If no extension info, try to get it from the filename itself
                if path_obj.suffix:
                    default_name = f"{base_name}_deidentified{path_obj.suffix}"
                else:
                    default_name = f"{base_name}_deidentified.csv"
        else:
            # Fallback for demo data or when no file info available
            default_name = "demo_deidentified.csv"

        # Open save file dialog
        file_picker.save_file(
            dialog_title="Save Deidentified Dataset",
            file_name=default_name,
            allowed_extensions=["csv", "xlsx", "dta"],
        )

    def _perform_anonymization_and_save(self, save_path):
        """Perform anonymization and save the file."""
        try:
            # Get file info and load dataset
            files = self.state_manager.state.selected_files
            if not files:
                self._show_dialog("No Data", "No dataset file is currently loaded.")
                return

            # Load the dataset into the adapter
            file_path = str(files[0].path)
            success, message = self.adapter.load_dataset(file_path)
            if not success:
                self._show_dialog("Load Error", f"Failed to load dataset: {message}")
                return

            # Get per-column anonymization methods and results from state
            column_methods = self.state_manager.state.column_anonymization_methods
            results = self.state_manager.state.detection_results

            # Perform per-column anonymization
            success, anonymized_df, report = (
                self.adapter.generate_per_column_anonymized_dataset(
                    column_methods=column_methods,
                    detection_results=results,
                )
            )

            if not success:
                self._show_dialog(
                    "Anonymization Failed", f"Failed to anonymize data: {report}"
                )
                return

            # Save the file
            # Determine file format and save accordingly
            if save_path.suffix.lower() == ".csv":
                anonymized_df.to_csv(save_path, index=False)
            elif save_path.suffix.lower() == ".xlsx":
                anonymized_df.to_excel(save_path, index=False)
            elif save_path.suffix.lower() == ".dta":
                anonymized_df.to_stata(save_path, write_index=False)
            else:
                # Default to CSV
                anonymized_df.to_csv(save_path, index=False)

            # Save the report alongside the data
            report_path = (
                save_path.parent / f"{save_path.stem}_anonymization_report.txt"
            )
            with open(report_path, "w") as f:
                f.write(report)

            # Show success dialog
            self._show_download_success_dialog(save_path)

        except Exception as ex:
            self._show_dialog(
                "Download Failed", f"Failed to download deidentified data:\n\n{str(ex)}"
            )

    def _show_download_success_dialog(self, save_path):
        """Show success dialog after download completes."""
        import platform
        import subprocess

        def close_dialog(e):
            dialog.open = False
            self.page.update()

        def open_folder(e):
            folder_path = save_path.parent
            if platform.system() == "Windows":
                subprocess.Popen(f'explorer /select,"{save_path}"')
            elif platform.system() == "Darwin":
                subprocess.Popen(["open", "-R", str(save_path)])
            else:
                subprocess.Popen(["xdg-open", str(folder_path)])
            close_dialog(e)

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Download Complete!", color=IPAColors.SUCCESS),
            content=ft.Column(
                [
                    ft.Icon(ft.Icons.CHECK_CIRCLE, color=IPAColors.SUCCESS, size=48),
                    ft.Text(
                        "Deidentified dataset has been saved successfully!",
                        text_align=ft.TextAlign.CENTER,
                    ),
                    ft.Text(
                        f"\nSaved to: {save_path.name}",
                        size=IPATypography.BODY_SMALL,
                        color=IPAColors.DARK_GREY,
                        text_align=ft.TextAlign.CENTER,
                        selectable=True,
                    ),
                    ft.Text(
                        f"\nReport: {save_path.stem}_anonymization_report.txt",
                        size=IPATypography.BODY_SMALL,
                        color=IPAColors.DARK_GREY,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    ft.Text(
                        "\nUsed per-column anonymization methods (see report for details)",
                        size=IPATypography.BODY_SMALL,
                        color=IPAColors.CHARCOAL,
                        text_align=ft.TextAlign.CENTER,
                        weight=ft.FontWeight.W_600,
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                tight=True,
                spacing=IPASpacing.SM,
            ),
            actions=[
                ft.TextButton("Open Folder", on_click=open_folder),
                ft.TextButton("Close", on_click=close_dialog),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        self.page.open(dialog)

    def _handle_generate_export(self, e):
        """Handle generate export button click."""

        # Use file picker to select export location
        def handle_export_result(e: ft.FilePickerResultEvent):
            if e.path:
                export_path = Path(e.path)
                self._perform_export(export_path)

        file_picker = ft.FilePicker(on_result=handle_export_result)
        self.page.overlay.append(file_picker)
        self.page.update()

        # Open directory picker
        file_picker.get_directory_path(dialog_title="Select Export Location")

    def _perform_export(self, export_dir: Path):
        """Perform the actual export operation."""
        try:
            # Create timestamped export folder
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            export_folder = export_dir / f"pii_analysis_{timestamp}"
            export_folder.mkdir(parents=True, exist_ok=True)

            # Generate report file
            report_path = export_folder / "pii_detection_report.txt"
            self._generate_report(report_path)

            # Show success dialog
            def close_dialog(e):
                dialog.open = False
                self.page.update()

            def open_folder(e):
                import platform
                import subprocess

                if platform.system() == "Windows":
                    subprocess.Popen(f'explorer "{export_folder}"')
                elif platform.system() == "Darwin":
                    subprocess.Popen(["open", str(export_folder)])
                else:
                    subprocess.Popen(["xdg-open", str(export_folder)])
                close_dialog(e)

            dialog = ft.AlertDialog(
                modal=True,
                title=ft.Text("Export Successful", color=IPAColors.SUCCESS),
                content=ft.Column(
                    [
                        ft.Icon(
                            ft.Icons.CHECK_CIRCLE, color=IPAColors.SUCCESS, size=48
                        ),
                        ft.Text(
                            "Analysis results exported to:",
                            text_align=ft.TextAlign.CENTER,
                        ),
                        ft.Text(
                            str(export_folder),
                            size=IPATypography.BODY_SMALL,
                            color=IPAColors.DARK_GREY,
                            text_align=ft.TextAlign.CENTER,
                            selectable=True,
                        ),
                        ft.Text(
                            "\nExported files:",
                            weight=ft.FontWeight.W_600,
                        ),
                        ft.Text(
                            "• pii_detection_report.txt - Detailed analysis report",
                            size=IPATypography.BODY_SMALL,
                        ),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    tight=True,
                    spacing=IPASpacing.SM,
                ),
                actions=[
                    ft.TextButton("Open Folder", on_click=open_folder),
                    ft.TextButton("Close", on_click=close_dialog),
                ],
                actions_alignment=ft.MainAxisAlignment.END,
            )

            self.page.open(dialog)

        except Exception as ex:
            self._show_dialog("Export Failed", f"Failed to export results: {str(ex)}")

    def _generate_report(self, report_path: Path):
        """Generate a text report of the analysis results."""
        results = self.state_manager.state.detection_results
        files = self.state_manager.state.selected_files

        with open(report_path, "w") as f:
            f.write("=" * 70 + "\n")
            f.write("PII DETECTION ANALYSIS REPORT\n")
            f.write("=" * 70 + "\n\n")

            # File information
            f.write("ANALYZED FILES\n")
            f.write("-" * 70 + "\n")
            for file_info in files:
                f.write(f"File: {file_info.name}\n")
                f.write(f"Path: {file_info.path}\n")
                f.write(f"Size: {file_info.size_mb:.2f} MB\n")
                f.write(f"Format: {file_info.format}\n\n")

            # Summary statistics
            f.write("\nDETECTION SUMMARY\n")
            f.write("-" * 70 + "\n")
            f.write(f"Total PII columns detected: {len(results)}\n")

            high_conf = sum(1 for r in results if r.confidence > 0.8)
            medium_conf = sum(1 for r in results if 0.5 <= r.confidence <= 0.8)
            low_conf = sum(1 for r in results if r.confidence < 0.5)

            f.write(f"  - High confidence (>0.8): {high_conf}\n")
            f.write(f"  - Medium confidence (0.5-0.8): {medium_conf}\n")
            f.write(f"  - Low confidence (<0.5): {low_conf}\n\n")

            # Detailed results
            f.write("\nDETAILED RESULTS\n")
            f.write("-" * 70 + "\n\n")

            for i, result in enumerate(results, 1):
                f.write(f"{i}. Column: {result.column}\n")
                f.write(f"   Detection Method: {result.method}\n")
                f.write(f"   Confidence Score: {result.confidence:.2%}\n")
                f.write(f"   PII Type: {result.pii_type}\n")
                if result.entity_types:
                    f.write(f"   Entity Types: {', '.join(result.entity_types)}\n")
                if result.details:
                    f.write(f"   Details: {result.details}\n")
                f.write("\n")

            # Recommendations
            f.write("\nRECOMMENDATIONS\n")
            f.write("-" * 70 + "\n")
            f.write("1. Review all detected PII columns carefully\n")
            f.write("2. Consider anonymizing or removing high-confidence PII columns\n")
            f.write("3. Manually verify medium and low confidence detections\n")
            f.write(
                "4. Ensure compliance with data protection regulations (GDPR, HIPAA, etc.)\n\n"
            )

            # Footer
            f.write("=" * 70 + "\n")
            f.write(f"Report generated: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("Generated by: IPA PII Detector\n")
            f.write("=" * 70 + "\n")

    def _show_dialog(self, title: str, message: str):
        """Show a dialog with the given title and message."""

        def close_dialog(e):
            dialog.open = False
            self.page.update()

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text(title),
            content=ft.Text(message),
            actions=[
                ft.TextButton("Close", on_click=close_dialog),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        self.page.open(dialog)

    def on_state_changed(self, state: AppState):
        """Handle state changes."""
        pass
