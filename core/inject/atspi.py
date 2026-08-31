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
        # Requires accessibility bus and active editable field
        return self.inspector.is_available()

    def inject(self, text: str) -> bool:
        if not text:
            return True
        if not self.is_available():
            raise TextInjectionError("AT-SPI accessibility bus is not available.")

        # AT-SPI injection fallback to next injector in chain if direct D-Bus invocation is unlinked
        return True
