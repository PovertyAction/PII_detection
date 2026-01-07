"""Custom button components following the IPA design system."""

from collections.abc import Callable

import flet as ft

from pii_detector.gui.flet_app.config.constants import (
    IPAColors,
    IPASpacing,
    IPATypography,
)


def create_primary_button(
    text: str,
    on_click: Callable | None = None,
    icon: str | None = None,
    width: float | None = None,
    disabled: bool = False,
) -> ft.ElevatedButton:
    """Create a primary action button.

    Args:
        text: Button text
        on_click: Click handler function
        icon: Optional icon name
        width: Optional button width
        disabled: Whether button is disabled

    Returns:
        Flet ElevatedButton with primary styling

    """
    return ft.ElevatedButton(
        text=text,
        icon=icon,
        on_click=on_click,
        width=width,
        height=44,  # Standard button height
        disabled=disabled,
        style=ft.ButtonStyle(
            bgcolor=IPAColors.IPA_GREEN if not disabled else IPAColors.DISABLED_COLOR,
            color=IPAColors.WHITE,
            overlay_color=IPAColors.DARK_GREEN,
            elevation=2,
            text_style=ft.TextStyle(
                size=IPATypography.BODY_LARGE,
                weight=ft.FontWeight.W_500,
            ),
            padding=ft.padding.symmetric(
                horizontal=IPASpacing.BUTTON_PADDING_H,
                vertical=IPASpacing.BUTTON_PADDING_V,
            ),
            shape=ft.RoundedRectangleBorder(radius=IPASpacing.RADIUS_SM),
        ),
    )


def create_secondary_button(
    text: str,
    on_click: Callable | None = None,
    icon: str | None = None,
    width: float | None = None,
    disabled: bool = False,
) -> ft.OutlinedButton:
    """Create a secondary action button.

    Args:
        text: Button text
        on_click: Click handler function
        icon: Optional icon name
        width: Optional button width
        disabled: Whether button is disabled

    Returns:
        Flet OutlinedButton with secondary styling

    """
    return ft.OutlinedButton(
        text=text,
        icon=icon,
        on_click=on_click,
        width=width,
        height=44,
        disabled=disabled,
        style=ft.ButtonStyle(
            color=IPAColors.IPA_GREEN if not disabled else IPAColors.DISABLED_COLOR,
            bgcolor=IPAColors.WHITE,
            overlay_color=IPAColors.BLUE_ACCENT,
            side=ft.BorderSide(
                color=IPAColors.IPA_GREEN if not disabled else IPAColors.DISABLED_COLOR,
                width=2,
            ),
            text_style=ft.TextStyle(
                size=IPATypography.BODY_LARGE,
                weight=ft.FontWeight.W_500,
            ),
            padding=ft.padding.symmetric(
                horizontal=IPASpacing.BUTTON_PADDING_H,
                vertical=IPASpacing.BUTTON_PADDING_V,
            ),
            shape=ft.RoundedRectangleBorder(radius=IPASpacing.RADIUS_SM),
        ),
    )


def create_danger_button(
    text: str,
    on_click: Callable | None = None,
    icon: str | None = None,
    width: float | None = None,
    disabled: bool = False,
) -> ft.ElevatedButton:
    """Create a danger/warning action button.

    Args:
        text: Button text
        on_click: Click handler function
        icon: Optional icon name
        width: Optional button width
        disabled: Whether button is disabled

    Returns:
        Flet ElevatedButton with danger styling

    """
    return ft.ElevatedButton(
        text=text,
        icon=icon,
        on_click=on_click,
        width=width,
        height=44,
        disabled=disabled,
        style=ft.ButtonStyle(
            bgcolor=IPAColors.RED_ORANGE if not disabled else IPAColors.DISABLED_COLOR,
            color=IPAColors.WHITE,
            overlay_color=IPAColors.RED_ORANGE + "CC",  # Darker overlay
            elevation=2,
            text_style=ft.TextStyle(
                size=IPATypography.BODY_LARGE,
                weight=ft.FontWeight.W_500,
            ),
            padding=ft.padding.symmetric(
                horizontal=IPASpacing.BUTTON_PADDING_H,
                vertical=IPASpacing.BUTTON_PADDING_V,
            ),
            shape=ft.RoundedRectangleBorder(radius=IPASpacing.RADIUS_SM),
        ),
    )


def create_icon_button(
    icon: str,
    tooltip: str,
    on_click: Callable | None = None,
    color: str = IPAColors.CHARCOAL,
    disabled: bool = False,
) -> ft.IconButton:
    """Create an icon-only button.

    Args:
        icon: Material Design icon name
        tooltip: Button tooltip text
        on_click: Click handler function
        color: Icon color
        disabled: Whether button is disabled

    Returns:
        Flet IconButton with styling

    """
    return ft.IconButton(
        icon=icon,
        tooltip=tooltip,
        on_click=on_click,
        icon_color=color if not disabled else IPAColors.DISABLED_COLOR,
        icon_size=20,
        disabled=disabled,
    )


def create_action_button_group(column_name: str, action_handlers: dict) -> ft.Row:
    """Create a group of action buttons for PII column actions.

    Args:
        column_name: Name of the column
        action_handlers: Dictionary of action handlers

    Returns:
        Flet Row with action buttons

    """
    return ft.Row(
        [
            ft.ElevatedButton(
                "Keep",
                icon=ft.Icons.CHECK_CIRCLE,
                on_click=lambda e: action_handlers.get("keep", lambda x: None)(
                    column_name
                ),
                style=ft.ButtonStyle(
                    bgcolor=IPAColors.DARK_GREY,
                    color=IPAColors.WHITE,
                    text_style=ft.TextStyle(size=IPATypography.BODY_SMALL),
                    padding=ft.padding.symmetric(horizontal=8, vertical=4),
                    shape=ft.RoundedRectangleBorder(radius=IPASpacing.RADIUS_SM),
                ),
                height=32,
            ),
            ft.ElevatedButton(
                "Anonymize",
                icon=ft.Icons.LOCK,
                on_click=lambda e: action_handlers.get("anonymize", lambda x: None)(
                    column_name
                ),
                style=ft.ButtonStyle(
                    bgcolor=IPAColors.IPA_GREEN,
                    color=IPAColors.WHITE,
                    text_style=ft.TextStyle(size=IPATypography.BODY_SMALL),
                    padding=ft.padding.symmetric(horizontal=8, vertical=4),
                    shape=ft.RoundedRectangleBorder(radius=IPASpacing.RADIUS_SM),
                ),
                height=32,
            ),
            ft.ElevatedButton(
                "Remove",
                icon=ft.Icons.DELETE,
                on_click=lambda e: action_handlers.get("remove", lambda x: None)(
                    column_name
                ),
                style=ft.ButtonStyle(
                    bgcolor=IPAColors.RED_ORANGE,
                    color=IPAColors.WHITE,
                    text_style=ft.TextStyle(size=IPATypography.BODY_SMALL),
                    padding=ft.padding.symmetric(horizontal=8, vertical=4),
                    shape=ft.RoundedRectangleBorder(radius=IPASpacing.RADIUS_SM),
                ),
                height=32,
            ),
        ],
        spacing=IPASpacing.XS,
        tight=True,
    )
