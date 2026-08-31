from dataclasses import dataclass
from typing import Optional
from .active_window import WindowContext

@dataclass
class StyleProfile:
    name: str
    auto_capitalize: bool = True
    auto_punctuate: bool = True
    enable_dev_operators: bool = False
    enable_casing_transforms: bool = False
    strip_trailing_period: bool = False
    paste_shortcut: str = "ctrl+v"  # "ctrl+v" or "ctrl+shift+v"

PROFILES = {
    "terminal": StyleProfile(
        name="terminal",
        auto_capitalize=False,
        auto_punctuate=False,
        enable_dev_operators=True,
        enable_casing_transforms=True,
        strip_trailing_period=True,
        paste_shortcut="ctrl+shift+v"
    ),
    "code": StyleProfile(
        name="code",
        auto_capitalize=True,
        auto_punctuate=True,
        enable_dev_operators=True,
        enable_casing_transforms=True,
        strip_trailing_period=False,
        paste_shortcut="ctrl+v"
    ),
    "chat": StyleProfile(
        name="chat",
        auto_capitalize=True,
        auto_punctuate=True,
        enable_dev_operators=False,
        enable_casing_transforms=False,
        strip_trailing_period=False,
        paste_shortcut="ctrl+v"
    ),
    "email": StyleProfile(
        name="email",
        auto_capitalize=True,
        auto_punctuate=True,
        enable_dev_operators=False,
        enable_casing_transforms=False,
        strip_trailing_period=False,
        paste_shortcut="ctrl+v"
    ),
    "document": StyleProfile(
        name="document",
        auto_capitalize=True,
        auto_punctuate=True,
        enable_dev_operators=False,
        enable_casing_transforms=False,
        strip_trailing_period=False,
        paste_shortcut="ctrl+v"
    ),
    "generic": StyleProfile(
        name="generic",
        auto_capitalize=True,
        auto_punctuate=True,
        enable_dev_operators=True,
        enable_casing_transforms=True,
        strip_trailing_period=False,
        paste_shortcut="ctrl+v"
    )
}

def get_style_profile_for_window(context: Optional[WindowContext]) -> StyleProfile:
    """Resolve active style profile from window context."""
    if not context or not context.app_category:
        return PROFILES["generic"]
    return PROFILES.get(context.app_category, PROFILES["generic"])
