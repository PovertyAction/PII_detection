"""Dashboard screen - main landing page with quick actions."""

import flet as ft

from pii_detector.gui.flet_app.config.constants import (
    AppConstants,
    IPAColors,
    IPASpacing,
    IPATypography,
)
from pii_detector.gui.flet_app.config.settings import AppState
from pii_detector.gui.flet_app.ui.components.cards import (
    create_action_card,
    create_status_card,
)


class DashboardScreen:
    """Dashboard screen implementation."""

    def __init__(self, page: ft.Page, state_manager):
        """Initialize the dashboard screen.

        Args:
            page: Flet page instance
            state_manager: Application state manager

        """
        self.page = page
        self.state_manager = state_manager
        self._screen_name = AppConstants.SCREEN_DASHBOARD

    def build(self) -> ft.Container:
        """Build the dashboard screen."""
        return ft.Container(
            content=ft.Column(
                [
                    # Quick Actions Section
                    self._build_quick_actions(),
                    # System Status Section
                    self._build_system_status(),
                ],
                spacing=IPASpacing.XL,
                scroll=ft.ScrollMode.AUTO,
            ),
            padding=IPASpacing.XL,
            expand=True,
        )

    def _build_quick_actions(self) -> ft.Container:
        """Build the quick actions grid."""
        return ft.Container(
            content=ft.Column(
                [
                    # Section title
                    ft.Text(
                        "Quick Actions",
                        size=IPATypography.HEADER_2,
                        weight=ft.FontWeight.W_600,
                        color=IPAColors.DARK_BLUE,
                    ),
                    # Action cards grid
                    ft.Row(
                        [
                            create_action_card(
                                title="Single Analysis",
                                description="Analyze one dataset file for PII detection and anonymization",
                                icon=ft.Icons.DESCRIPTION,
                                on_click_handler=self._handle_single_analysis,
                            ),
                            create_action_card(
                                title="Batch Process",
                                description="Process multiple dataset files in parallel for efficient workflow",
                                icon=ft.Icons.BAR_CHART,
                                on_click_handler=self._handle_batch_process,
                                enabled=False,  # Feature disabled - focusing on single analysis
                            ),
                            create_action_card(
                                title="Recent Projects",
                                description="View and reopen previously analyzed datasets and results",
                                icon=ft.Icons.HISTORY,
                                on_click_handler=self._handle_recent_projects,
                                enabled=False,  # Feature not implemented yet
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                        spacing=IPASpacing.LG,
                    ),
                ],
                spacing=IPASpacing.MD,
            ),
        )

    def _build_system_status(self) -> ft.Container:
        """Build the system status panel."""
        return ft.Container(
            content=ft.Column(
                [
                    # Section title
                    ft.Text(
                        "System Status",
                        size=IPATypography.BODY_LARGE,
                        weight=ft.FontWeight.W_600,
                        color=IPAColors.CHARCOAL,
                    ),
                    # Status indicators
                    ft.Column(
                        [
                            create_status_card(
                                title="Detection Methods",
                                status="Active",
                                details="Standard and AI detection available",
                                status_color=IPAColors.SUCCESS,
                            ),
                            create_status_card(
                                title="Last Processing",
                                status="Idle",
                                details="No recent processing activity",
                                status_color=IPAColors.DARK_GREY,
                            ),
                            create_status_card(
                                title="Performance",
                                status="Optimal",
                                details="All systems running normally",
                                status_color=IPAColors.SUCCESS,
                            ),
                        ],
                        spacing=IPASpacing.SM,
                    ),
                ],
                spacing=IPASpacing.MD,
            ),
            padding=IPASpacing.MD,
            bgcolor=IPAColors.WHITE,
            border=ft.border.all(1, IPAColors.DARK_GREY),
            border_radius=IPASpacing.RADIUS_MD,
        )

    def _handle_single_analysis(self, e):
        """Handle single analysis action."""
        # print("DEBUG: Single analysis clicked!")  # Debug output
        # Clear any previous file selections for single analysis
        self.state_manager.update_state(selected_files=[])
        # print("DEBUG: About to navigate to file selection")  # Debug output
        self.state_manager.navigate_to(AppConstants.SCREEN_FILE_SELECTION)
        # print("DEBUG: Navigation complete")  # Debug output

    def _handle_batch_process(self, e):
        """Handle batch process action."""
        # Clear any previous file selections for batch processing
        self.state_manager.update_state(selected_files=[])
        # Navigate to file selection with batch mode indication
        # For now, use the same file selection screen
        self.state_manager.navigate_to(AppConstants.SCREEN_FILE_SELECTION)

    def _handle_recent_projects(self, e):
        """Handle recent projects action."""

        # Placeholder for recent projects functionality
        def close_dialog(e):
            dialog.open = False
            self.page.update()

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Recent Projects"),
            content=ft.Text(
                "Recent projects functionality is coming soon. This will show your previously analyzed datasets and allow you to reopen results."
            ),
            actions=[
                ft.TextButton("Close", on_click=close_dialog),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        self.page.dialog = dialog
        dialog.open = True
        self.page.update()

    def on_state_changed(self, state: AppState):
        """Handle state changes.

        Args:
            state: Updated application state

        """
        # Dashboard doesn't need to react to most state changes
        # but we could update the status panel based on recent activity
        pass
