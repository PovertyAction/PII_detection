"""Reusable card components following the IPA design system."""

from collections.abc import Callable

import flet as ft

from pii_detector.gui.flet_app.config.constants import (
    IPAColors,
    IPASpacing,
    IPATypography,
)


def create_action_card(
    title: str,
    description: str,
    icon: str,
    on_click_handler: Callable | None = None,
    enabled: bool = True,
) -> ft.Container:
    """Create an action card for the dashboard.

    Args:
        title: Card title text
        description: Card description text
        icon: Material Design icon name
        on_click_handler: Optional click handler function
        enabled: Whether the card is interactive

    Returns:
        Flet Container with action card styling

    """
    # Determine colors based on enabled state
    bg_color = IPAColors.LIGHT_GREY if enabled else IPAColors.DISABLED_COLOR
    border_color = IPAColors.DARK_GREY if enabled else IPAColors.DISABLED_COLOR
    text_color = IPAColors.CHARCOAL if enabled else IPAColors.DARK_GREY

    def handle_hover(e):
        if enabled:
            if e.data == "true":  # Mouse enter
                card.bgcolor = IPAColors.BLUE_ACCENT
                card.border = ft.border.all(2, IPAColors.IPA_GREEN)
            else:  # Mouse leave
                card.bgcolor = IPAColors.LIGHT_GREY
                card.border = ft.border.all(2, IPAColors.DARK_GREY)
            card.update()

    card = ft.Container(
        content=ft.Column(
            [
                # Icon container
                ft.Container(
                    content=ft.Icon(icon, size=24, color=IPAColors.WHITE),
                    width=60,
                    height=60,
                    bgcolor=IPAColors.IPA_GREEN if enabled else IPAColors.DARK_GREY,
                    border_radius=30,
                    alignment=ft.alignment.center,
                ),
                # Title text
                ft.Text(
                    title,
                    size=IPATypography.HEADER_3,
                    weight=ft.FontWeight.W_600,
                    color=text_color,
                    text_align=ft.TextAlign.CENTER,
                ),
                # Description text
                ft.Text(
                    description,
                    size=IPATypography.BODY_SMALL,
                    color=text_color,
                    text_align=ft.TextAlign.CENTER,
                    max_lines=4,
                    overflow=ft.TextOverflow.ELLIPSIS,
                ),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=IPASpacing.MD,
        ),
        width=200,
        height=220,
        padding=IPASpacing.XL,
        bgcolor=bg_color,
        border=ft.border.all(2, border_color),
        border_radius=IPASpacing.RADIUS_LG,
        on_click=on_click_handler if enabled else None,
        on_hover=handle_hover if enabled else None,
        tooltip=title if enabled else "Feature disabled",
    )

    return card


def create_metric_card(
    title: str,
    value: str,
    subtitle: str | None = None,
    color: str = IPAColors.IPA_GREEN,
    icon: str | None = None,
) -> ft.Container:
    """Create a metric display card.

    Args:
        title: Metric title
        value: Metric value (number or text)
        subtitle: Optional subtitle text
        color: Color theme for the card
        icon: Optional icon name

    Returns:
        Flet Container with metric card styling

    """
    content_items = []

    # Add icon if provided
    if icon:
        content_items.append(
            ft.Icon(
                icon,
                size=32,
                color=color,
            )
        )

    # Value text (large)
    content_items.append(
        ft.Text(
            value,
            size=IPATypography.HEADER_2,
            weight=ft.FontWeight.BOLD,
            color=color,
        )
    )

    # Title text
    content_items.append(
        ft.Text(
            title,
            size=IPATypography.BODY_REGULAR,
            weight=ft.FontWeight.W_500,
            color=IPAColors.CHARCOAL,
        )
    )

    # Subtitle if provided
    if subtitle:
        content_items.append(
            ft.Text(
                subtitle,
                size=IPATypography.BODY_SMALL,
                color=IPAColors.DARK_GREY,
            )
        )

    return ft.Container(
        content=ft.Column(
            content_items,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=IPASpacing.SM,
        ),
        padding=IPASpacing.MD,
        bgcolor=IPAColors.WHITE,
        border=ft.border.all(1, IPAColors.DARK_GREY),
        border_radius=IPASpacing.RADIUS_MD,
        alignment=ft.alignment.center,
    )


def create_status_card(
    title: str, status: str, details: str, status_color: str = IPAColors.IPA_GREEN
) -> ft.Container:
    """Create a system status card.

    Args:
        title: Status category title
        status: Status text (e.g., "Active", "Warning")
        details: Additional status details
        status_color: Color for the status indicator

    Returns:
        Flet Container with status card styling

    """
    return ft.Container(
        content=ft.Row(
            [
                # Status indicator dot
                ft.Container(
                    width=12,
                    height=12,
                    bgcolor=status_color,
                    border_radius=6,
                ),
                # Status content
                ft.Column(
                    [
                        ft.Text(
                            title,
                            size=IPATypography.BODY_REGULAR,
                            weight=ft.FontWeight.W_500,
                            color=IPAColors.CHARCOAL,
                        ),
                        ft.Text(
                            f"{status} - {details}",
                            size=IPATypography.BODY_SMALL,
                            color=IPAColors.CHARCOAL,
                        ),
                    ],
                    spacing=2,
                ),
            ],
            spacing=IPASpacing.SM,
            alignment=ft.MainAxisAlignment.START,
        ),
        padding=IPASpacing.SM,
    )
