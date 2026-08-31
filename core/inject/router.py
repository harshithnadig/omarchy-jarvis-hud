from typing import Dict, List, Optional
from .base import TextInjector, TextInjectionError
from .atspi import AtspiInjector
from .wtype import WtypeInjector
from .clipboard import SafeClipboardInjector
from .ydotool import YdotoolInjector
from .xdotool import XdotoolInjector

class InjectorRouter:
    """
    Manages text injection backends for Linux / Wayland / X11:
    - atspi: Direct accessible text insertion without synthetic keystrokes
    - wtype: Fast direct typing on wlroots/Hyprland (Primary Wayland)
    - ydotool: Uinput virtual keyboard typing
    - xdotool: X11 / XWayland compatibility fallback
    - clipboard: Safe clipboard preservation & paste (Universal fallback)
    """
    def __init__(self, preferred_method: str = "auto"):
        self.preferred_method = preferred_method
        self._injectors: Dict[str, TextInjector] = {
            "atspi": AtspiInjector(),
            "wtype": WtypeInjector(delay_ms=0),
            "ydotool": YdotoolInjector(key_delay_ms=0),
            "xdotool": XdotoolInjector(key_delay_ms=0),
            "clipboard": SafeClipboardInjector(restore_delay_ms=120),
        }

    def get_injector(self, method: Optional[str] = None) -> TextInjector:
        target = (method or self.preferred_method).lower().strip()

        if target in ("atspi", "accessibility"):
            inj = self._injectors["atspi"]
            if inj.is_available():
                return inj
            raise TextInjectionError("AT-SPI accessibility injection is not available on this system.")

        if target in ("wtype", "direct"):
            inj = self._injectors["wtype"]
            if inj.is_available():
                return inj
            raise TextInjectionError("Direct typing backend (wtype) is not available on this system.")

        if target in ("clipboard", "paste"):
            inj = self._injectors["clipboard"]
            if inj.is_available():
                return inj
            raise TextInjectionError("Safe clipboard injection is not available on this system.")

        if target == "ydotool":
            inj = self._injectors["ydotool"]
            if inj.is_available():
                return inj
            raise TextInjectionError("ydotool backend is not available on this system.")

        if target == "xdotool":
            inj = self._injectors["xdotool"]
            if inj.is_available():
                return inj
            raise TextInjectionError("xdotool backend is not available on this system.")

        if target in ("auto", "default", ""):
            # Fallback priority hierarchy: wtype -> ydotool -> xdotool -> safe clipboard
            for candidate in ("wtype", "ydotool", "xdotool", "clipboard"):
                if self._injectors[candidate].is_available():
                    return self._injectors[candidate]
            raise TextInjectionError("No compatible text injector found for this environment.")

        raise TextInjectionError(
            f"Unknown text injection method: '{target}'. Available: ['auto', 'atspi', 'wtype', 'ydotool', 'xdotool', 'clipboard']"
        )

    def inject_text(self, text: str, method: Optional[str] = None, paste_shortcut: str = "ctrl+v") -> bool:
        injector = self.get_injector(method)
        if isinstance(injector, SafeClipboardInjector):
            return injector.inject(text, paste_shortcut=paste_shortcut)
        return injector.inject(text)
