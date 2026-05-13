from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping


class BioMedPilotColors:
    """Cross-module color tokens for BioMedPilot UI surfaces."""

    PRIMARY_NAVY = "#12324A"
    ACCENT_TEAL = "#1BAE9F"
    BACKGROUND_LIGHT = "#F5F7F9"
    SURFACE_WHITE = "#FFFFFF"

    SURFACE_MUTED = "#F8FAFC"
    TEXT_PRIMARY = "#1F2933"
    TEXT_SECONDARY = "#6B7280"
    TEXT_INVERSE = "#FFFFFF"
    BORDER_SUBTLE = "#DDE3EA"
    BORDER_MEDIUM = "#D8DEE9"

    BIO_SOFT = "#EAF2F8"
    TEAL_SOFT = "#E7F7F5"
    TEAL_BORDER = "#BCE7E2"
    WARNING_SOFT = "#FFF7E6"
    WARNING_BORDER = "#F5D899"
    ERROR_SOFT = "#FFF1F0"
    ERROR_BORDER = "#FFD0CC"
    DRAFT_SOFT = "#F4F8FB"
    DISABLED_TEXT = "#94A3B8"

    STATUS_READY = "#0E6F66"
    STATUS_WARNING = "#D99A00"
    STATUS_ERROR = "#D43832"
    STATUS_DRAFT = "#6B7280"
    STATUS_CONFIRMED = PRIMARY_NAVY
    STATUS_RUNNING = ACCENT_TEAL
    STATUS_COMPLETED = "#22A66B"

    META_LEGACY = "#6B4FD8"
    META_LEGACY_SOFT = "#F0EDFF"


class BioMedPilotTypography:
    """Desktop typography scale in px."""

    APP_TITLE = 24
    HERO_TITLE = 24
    PAGE_TITLE = 18
    SECTION_TITLE = 18
    CARD_TITLE = 16
    BODY_TEXT = 13
    HELPER_TEXT = 12
    STATUS_TEXT = 12
    BUTTON_TEXT = 13
    CAPTION = 11


class BioMedPilotSpacing:
    """Shared spacing scale in px."""

    XS = 4
    SM = 8
    MD = 12
    LG = 16
    XL = 24
    XXL = 32


class BioMedPilotRadii:
    """Shared corner radii in px."""

    SMALL = 8
    CARD = 8
    MEDIUM = 14
    LARGE = 20


class BioMedPilotControlHeights:
    """Shared form and action control heights in px."""

    FIELD = 38
    BUTTON = 38
    PRIMARY = 42


class BioMedPilotButtonRoles:
    """Canonical action roles for future shared button components."""

    PRIMARY_ACTION = "primary_action"
    SECONDARY_ACTION = "secondary_action"
    QUIET_ACTION = "quiet_action"
    DESTRUCTIVE_ACTION = "destructive_action"
    NAVIGATION_NEXT = "navigation_next"
    NAVIGATION_BACK = "navigation_back"
    DETAIL_ACTION = "detail_action"
    CONFIRM_ACTION = "confirm_action"


@dataclass(frozen=True)
class BioMedPilotStatusStyle:
    text: str
    background: str
    border: str
    label_zh: str


class BioMedPilotStatusColors:
    READY = BioMedPilotStatusStyle(
        text=BioMedPilotColors.STATUS_READY,
        background=BioMedPilotColors.TEAL_SOFT,
        border=BioMedPilotColors.TEAL_BORDER,
        label_zh="已就绪",
    )
    NOT_READY = BioMedPilotStatusStyle(
        text=BioMedPilotColors.TEXT_SECONDARY,
        background=BioMedPilotColors.SURFACE_MUTED,
        border=BioMedPilotColors.BORDER_SUBTLE,
        label_zh="未就绪",
    )
    WARNING = BioMedPilotStatusStyle(
        text=BioMedPilotColors.STATUS_WARNING,
        background=BioMedPilotColors.WARNING_SOFT,
        border=BioMedPilotColors.WARNING_BORDER,
        label_zh="需注意",
    )
    ERROR = BioMedPilotStatusStyle(
        text=BioMedPilotColors.STATUS_ERROR,
        background=BioMedPilotColors.ERROR_SOFT,
        border=BioMedPilotColors.ERROR_BORDER,
        label_zh="错误",
    )
    DRAFT = BioMedPilotStatusStyle(
        text=BioMedPilotColors.STATUS_DRAFT,
        background=BioMedPilotColors.DRAFT_SOFT,
        border=BioMedPilotColors.BORDER_SUBTLE,
        label_zh="草稿",
    )
    CONFIRMED = BioMedPilotStatusStyle(
        text=BioMedPilotColors.STATUS_CONFIRMED,
        background=BioMedPilotColors.BIO_SOFT,
        border=BioMedPilotColors.BORDER_SUBTLE,
        label_zh="已确认",
    )
    RUNNING = BioMedPilotStatusStyle(
        text=BioMedPilotColors.STATUS_RUNNING,
        background=BioMedPilotColors.TEAL_SOFT,
        border=BioMedPilotColors.TEAL_BORDER,
        label_zh="运行中",
    )
    COMPLETED = BioMedPilotStatusStyle(
        text=BioMedPilotColors.STATUS_COMPLETED,
        background=BioMedPilotColors.TEAL_SOFT,
        border=BioMedPilotColors.TEAL_BORDER,
        label_zh="已完成",
    )
    TESTING = BioMedPilotStatusStyle(
        text=BioMedPilotColors.PRIMARY_NAVY,
        background=BioMedPilotColors.BIO_SOFT,
        border=BioMedPilotColors.BORDER_SUBTLE,
        label_zh="测试中",
    )
    BLOCKED = BioMedPilotStatusStyle(
        text=BioMedPilotColors.STATUS_ERROR,
        background=BioMedPilotColors.ERROR_SOFT,
        border=BioMedPilotColors.ERROR_BORDER,
        label_zh="受阻",
    )


_STATUS_STYLES: Mapping[str, BioMedPilotStatusStyle] = MappingProxyType(
    {
        "ready": BioMedPilotStatusColors.READY,
        "not_ready": BioMedPilotStatusColors.NOT_READY,
        "warning": BioMedPilotStatusColors.WARNING,
        "error": BioMedPilotStatusColors.ERROR,
        "draft": BioMedPilotStatusColors.DRAFT,
        "confirmed": BioMedPilotStatusColors.CONFIRMED,
        "running": BioMedPilotStatusColors.RUNNING,
        "completed": BioMedPilotStatusColors.COMPLETED,
        "testing": BioMedPilotStatusColors.TESTING,
        "blocked": BioMedPilotStatusColors.BLOCKED,
    }
)


def status_style(status: str) -> BioMedPilotStatusStyle:
    normalized = status.strip().lower().replace("-", "_").replace(" ", "_")
    return _STATUS_STYLES.get(normalized, BioMedPilotStatusColors.NOT_READY)


def status_styles() -> dict[str, BioMedPilotStatusStyle]:
    return dict(_STATUS_STYLES)


def surface_card_qss(selector: str = "QFrame") -> str:
    return (
        f"{selector} {{ "
        f"border: 1px solid {BioMedPilotColors.BORDER_MEDIUM}; "
        f"border-radius: {BioMedPilotRadii.CARD}px; "
        f"background: {BioMedPilotColors.SURFACE_WHITE}; "
        "}"
    )


def page_title_qss() -> str:
    return f"font-size: {BioMedPilotTypography.SECTION_TITLE + 2}px; font-weight: 700;"


def card_title_qss() -> str:
    return "font-weight: 700;"


def helper_text_qss() -> str:
    return f"color: {BioMedPilotColors.TEXT_SECONDARY};"


def error_text_qss() -> str:
    return f"color: {BioMedPilotColors.STATUS_ERROR};"


def warning_text_qss() -> str:
    return f"color: {BioMedPilotColors.STATUS_WARNING};"


def shell_sidebar_qss() -> str:
    return (
        "QFrame { "
        f"background: {BioMedPilotColors.SURFACE_MUTED}; "
        f"border-right: 1px solid {BioMedPilotColors.BORDER_MEDIUM}; "
        "}"
        "QPushButton { "
        "text-align: left; "
        f"padding: {BioMedPilotSpacing.SM}px 10px; "
        "border: 0; "
        "border-radius: 6px; "
        "}"
        "QPushButton:hover { "
        f"background: {BioMedPilotColors.BIO_SOFT}; "
        "}"
    )


def as_legacy_color_dict() -> dict[str, str]:
    return {
        "background": BioMedPilotColors.BACKGROUND_LIGHT,
        "surface": BioMedPilotColors.SURFACE_WHITE,
        "surface_muted": BioMedPilotColors.SURFACE_MUTED,
        "border": BioMedPilotColors.BORDER_SUBTLE,
        "text": BioMedPilotColors.TEXT_PRIMARY,
        "muted": BioMedPilotColors.TEXT_SECONDARY,
        "bio": BioMedPilotColors.PRIMARY_NAVY,
        "bio_soft": BioMedPilotColors.BIO_SOFT,
        "bio_accent": BioMedPilotColors.ACCENT_TEAL,
        "meta": BioMedPilotColors.META_LEGACY,
        "meta_soft": BioMedPilotColors.META_LEGACY_SOFT,
        "warning_soft": BioMedPilotColors.WARNING_SOFT,
        "warning": BioMedPilotColors.STATUS_WARNING,
        "success": BioMedPilotColors.STATUS_COMPLETED,
        "danger": BioMedPilotColors.STATUS_ERROR,
    }


def as_legacy_spacing_dict() -> dict[str, int]:
    return {
        "xs": BioMedPilotSpacing.XS,
        "sm": BioMedPilotSpacing.SM,
        "md": BioMedPilotSpacing.MD,
        "lg": BioMedPilotSpacing.LG,
        "xl": BioMedPilotSpacing.XL,
        "xxl": BioMedPilotSpacing.XXL,
    }


def as_legacy_control_height_dict() -> dict[str, int]:
    return {
        "field": BioMedPilotControlHeights.FIELD,
        "button": BioMedPilotControlHeights.BUTTON,
        "primary": BioMedPilotControlHeights.PRIMARY,
    }


def as_legacy_radius_dict() -> dict[str, int]:
    return {
        "sm": BioMedPilotRadii.SMALL,
        "md": BioMedPilotRadii.MEDIUM,
        "lg": BioMedPilotRadii.LARGE,
    }


def as_legacy_font_size_dict() -> dict[str, int]:
    return {
        "app_title": BioMedPilotTypography.APP_TITLE,
        "page_title": BioMedPilotTypography.PAGE_TITLE,
        "card_title": BioMedPilotTypography.CARD_TITLE,
        "body": BioMedPilotTypography.BODY_TEXT,
        "secondary": BioMedPilotTypography.HELPER_TEXT,
        "caption": BioMedPilotTypography.CAPTION,
        "hero": BioMedPilotTypography.HERO_TITLE,
    }
