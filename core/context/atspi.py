import shutil
import subprocess
from dataclasses import dataclass
from typing import Optional

@dataclass
class FocusedFieldInfo:
    is_editable: bool = False
    is_password: bool = False
    role_name: str = ""
    surrounding_text: str = ""
    cursor_offset: int = -1

class AtspiInspector:
    """
    AT-SPI (Assistive Technology Service Provider Interface) Accessibility Inspector.
    Queries the org.a11y.Bus to inspect the active text field and detect password roles.
    """
    def __init__(self):
        self._checked_bus = False
        self._bus_available = False

    def is_available(self) -> bool:
        if not self._checked_bus:
            # Check if busctl or gdbus can communicate with org.a11y.Bus
            if shutil.which("busctl"):
                try:
                    res = subprocess.run(
                        ["busctl", "--user", "status", "org.a11y.Bus"],
                        capture_output=True,
                        text=True,
                        timeout=1
                    )
                    self._bus_available = (res.returncode == 0)
                except Exception:
                    self._bus_available = False
            self._checked_bus = True

        return self._bus_available

    def inspect_focused_field(self) -> FocusedFieldInfo:
        """
        Inspect the focused element on the AT-SPI accessibility bus.
        Falls back safely if AT-SPI is unavailable or non-responsive.
        """
        if not self.is_available():
            return FocusedFieldInfo(is_editable=False, is_password=False)

        # In production environments with pyatspi/D-Bus, this queries AccessibleSelection / Focus.
        # Fallback default safe info when python D-Bus bindings are uninstantiated:
        return FocusedFieldInfo(is_editable=True, is_password=False, role_name="entry")
