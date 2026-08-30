from typing import Dict, List, Optional
from .base import TextInjector, TextInjectionError
from .wtype import WtypeInjector
from .clipboard import SafeClipboardInjector

class InjectorRouter:
    """
    Manages text injection backends for Linux / Wayland.
    Prioritizes direct keystroke typing (wtype) and falls back to safe clipboard paste.
    """
    def __init__(self, preferred_method: str = "auto"):
        self.preferred_method = preferred_method
        self._injectors: Dict[str, TextInjector] = {
            "wtype": WtypeInjector(delay_ms=0),
            "clipboard": SafeClipboardInjector(restore_delay_ms=120)
        }

    def get_injector(self, method: Optional[str] = None) -> TextInjector:
        target = (method or self.preferred_method).lower().strip()

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

        if target in ("auto", "default", ""):
            # "auto" detection: prefer wtype, fall back to safe clipboard
            if self._injectors["wtype"].is_available():
                return self._injectors["wtype"]
            if self._injectors["clipboard"].is_available():
                return self._injectors["clipboard"]
            raise TextInjectionError("No compatible text injector found for this Wayland environment.")

        raise TextInjectionError(
            f"Unknown text injection method: '{target}'. Available: ['auto', 'wtype', 'clipboard']"
        )

    def inject_text(self, text: str, method: Optional[str] = None) -> bool:
        injector = self.get_injector(method)
        return injector.inject(text)
