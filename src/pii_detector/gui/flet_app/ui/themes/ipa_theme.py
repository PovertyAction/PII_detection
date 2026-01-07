"""IPA theme implementation for Flet application."""

import flet as ft

from pii_detector.gui.flet_app.config.constants import IPAColors, IPATypography


def create_ipa_theme() -> ft.Theme:
    """Create Flet theme with IPA color palette and typography."""
    return ft.Theme(
        color_scheme=ft.ColorScheme(
            # Primary colors
            primary=IPAColors.IPA_GREEN,
            primary_container=IPAColors.LIGHT_BLUE,
            on_primary=IPAColors.WHITE,
            on_primary_container=IPAColors.CHARCOAL,
            # Secondary colors
            secondary=IPAColors.DARK_BLUE,
            secondary_container=IPAColors.BLUE_ACCENT,
            on_secondary=IPAColors.WHITE,
            on_secondary_container=IPAColors.CHARCOAL,
            # Surface colors
            surface=IPAColors.WHITE,
            surface_variant=IPAColors.LIGHT_GREY,
            on_surface=IPAColors.CHARCOAL,
            on_surface_variant=IPAColors.DARK_GREY,
            # Background
            background=IPAColors.LIGHT_GREY,
            on_background=IPAColors.CHARCOAL,
            # Error colors
            error=IPAColors.RED_ORANGE,
            on_error=IPAColors.WHITE,
            error_container=IPAColors.RED_ORANGE + "20",  # 20% opacity
            on_error_container=IPAColors.RED_ORANGE,
            # Additional colors
            outline=IPAColors.DARK_GREY,
            outline_variant=IPAColors.LIGHT_GREY,
            shadow=IPAColors.CHARCOAL + "40",  # 40% opacity
        ),
        text_theme=ft.TextTheme(
            # Display styles
            display_large=ft.TextStyle(
                size=IPATypography.HEADER_1,
                color=IPAColors.DARK_BLUE,
                weight=ft.FontWeight.BOLD,
                font_family=IPATypography.PRIMARY_FONT,
            ),
            display_medium=ft.TextStyle(
                size=IPATypography.HEADER_2,
                color=IPAColors.DARK_BLUE,
                weight=ft.FontWeight.W_600,
                font_family=IPATypography.PRIMARY_FONT,
            ),
            display_small=ft.TextStyle(
                size=IPATypography.HEADER_3,
                color=IPAColors.CHARCOAL,
                weight=ft.FontWeight.W_600,
                font_family=IPATypography.PRIMARY_FONT,
            ),
            # Headline styles
            headline_large=ft.TextStyle(
                size=IPATypography.HEADER_1,
                color=IPAColors.DARK_BLUE,
                weight=ft.FontWeight.BOLD,
                font_family=IPATypography.PRIMARY_FONT,
            ),
            headline_medium=ft.TextStyle(
                size=IPATypography.HEADER_2,
                color=IPAColors.CHARCOAL,
                weight=ft.FontWeight.W_600,
                font_family=IPATypography.PRIMARY_FONT,
            ),
            headline_small=ft.TextStyle(
                size=IPATypography.HEADER_3,
                color=IPAColors.CHARCOAL,
                weight=ft.FontWeight.W_500,
                font_family=IPATypography.PRIMARY_FONT,
            ),
            # Title styles
            title_large=ft.TextStyle(
                size=IPATypography.BODY_LARGE,
                color=IPAColors.CHARCOAL,
                weight=ft.FontWeight.W_500,
                font_family=IPATypography.PRIMARY_FONT,
            ),
            title_medium=ft.TextStyle(
                size=IPATypography.BODY_REGULAR,
                color=IPAColors.CHARCOAL,
                weight=ft.FontWeight.W_500,
                font_family=IPATypography.PRIMARY_FONT,
            ),
            title_small=ft.TextStyle(
                size=IPATypography.BODY_SMALL,
                color=IPAColors.CHARCOAL,
                weight=ft.FontWeight.W_500,
                font_family=IPATypography.PRIMARY_FONT,
            ),
            # Body styles
            body_large=ft.TextStyle(
                size=IPATypography.BODY_LARGE,
                color=IPAColors.CHARCOAL,
                font_family=IPATypography.PRIMARY_FONT,
            ),
            body_medium=ft.TextStyle(
                size=IPATypography.BODY_REGULAR,
                color=IPAColors.CHARCOAL,
                font_family=IPATypography.PRIMARY_FONT,
            ),
            body_small=ft.TextStyle(
                size=IPATypography.BODY_SMALL,
                color=IPAColors.DARK_GREY,
                font_family=IPATypography.PRIMARY_FONT,
            ),
            # Label styles
            label_large=ft.TextStyle(
                size=IPATypography.BODY_REGULAR,
                color=IPAColors.CHARCOAL,
                weight=ft.FontWeight.W_500,
                font_family=IPATypography.PRIMARY_FONT,
            ),
            label_medium=ft.TextStyle(
                size=IPATypography.BODY_SMALL,
                color=IPAColors.CHARCOAL,
                weight=ft.FontWeight.W_500,
                font_family=IPATypography.PRIMARY_FONT,
            ),
            label_small=ft.TextStyle(
                size=10,
                color=IPAColors.DARK_GREY,
                weight=ft.FontWeight.W_500,
                font_family=IPATypography.PRIMARY_FONT,
            ),
        ),
        # Visual density
        visual_density=ft.VisualDensity.STANDARD,
    )
