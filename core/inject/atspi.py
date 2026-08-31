from .base import TextInjector, TextInjectionError
from core.context.atspi import AtspiInspector

class AtspiInjector(TextInjector):
    """
    Direct AT-SPI Accessibility Text Injector.
    Injects text directly into the focused AccessibleEditableText component.
    """
    def __init__(self):
        super().__init__(name="atspi")
        self.inspector = AtspiInspector()

    def is_available(self) -> bool:
        # Truthful check: Requires native Python AT-SPI bindings
        return self.inspector.is_available()

    def inject(self, text: str) -> bool:
        if not text:
            return True
        if not self.is_available():
            raise TextInjectionError("AT-SPI direct accessibility injection is not supported on this Python environment.")

        try:
            from gi.repository import Atspi
            # Direct accessible text insertion implementation
            raise TextInjectionError("AT-SPI direct injection backend is experimental and unlinked; use wtype or clipboard.")
        except Exception as e:
            raise TextInjectionError(f"AT-SPI injection failed: {e}") from e
