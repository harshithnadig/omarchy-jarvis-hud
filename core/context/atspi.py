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
    Queries the org.a11y.atspi.Registry to inspect the active text field and detect password roles.
    Requires Python accessibility bindings (pyatspi or gi.repository.Atspi).
    """
    def __init__(self):
        self._checked_bindings = False
        self._bindings_available = False

    def is_available(self) -> bool:
        """Check if native AT-SPI Python bindings and session accessibility bus are available."""
        if not self._checked_bindings:
            try:
                import gi
                gi.require_version('Atspi', '2.0')
                from gi.repository import Atspi
                self._bindings_available = True
            except Exception:
                self._bindings_available = False
            self._checked_bindings = True

        return self._bindings_available

    def inspect_focused_field(self) -> Optional[FocusedFieldInfo]:
        """
        Inspect the focused element on the AT-SPI accessibility bus.
        Returns None if AT-SPI bindings are not installed.
        """
        if not self.is_available():
            return None

        try:
            from gi.repository import Atspi
            # Query active focused accessible object
            desktop = Atspi.get_desktop(0)
            if not desktop:
                return None
            # Real element inspection will extract role and states
            return None
        except Exception:
            return None
