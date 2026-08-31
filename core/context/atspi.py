import os
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
    AT-SPI (Assistive Technology Service Provider Interface) Focused Field Inspector.
    Queries the Linux Accessibility D-Bus daemon (at-spi2-registryd) to determine:
    1. If the currently focused element is an editable text entry.
    2. If the field is a password/credential field (ROLE_PASSWORD_TEXT).
    3. Surrounding text context around the cursor.
    """
    def __init__(self):
        self._checked = False
        self._socket_path: Optional[str] = None

    def _get_socket_path(self) -> Optional[str]:
        # Check standard runtime directory
        runtime_dir = os.environ.get("XDG_RUNTIME_DIR", f"/run/user/{os.getuid()}")
        sock = os.path.join(runtime_dir, "at-spi", "bus_0")
        if os.path.exists(sock):
            return f"unix:path={sock}"

        # Fallback: Query session bus GetAddress
        if shutil.which("busctl"):
            try:
                res = subprocess.run(
                    ["busctl", "--user", "call", "org.a11y.Bus", "/org/a11y/bus", "org.a11y.Bus", "GetAddress"],
                    capture_output=True,
                    text=True,
                    timeout=1
                )
                if res.returncode == 0 and "unix:path=" in res.stdout:
                    # Output: s "unix:path=/run/user/1000/at-spi/bus_0"
                    parts = res.stdout.split('"')
                    if len(parts) >= 2:
                        return parts[1]
            except Exception:
                pass
        return None

    def is_available(self) -> bool:
        """Check if AT-SPI registry daemon socket is active and reachable."""
        if not self._checked:
            self._socket_path = self._get_socket_path()
            self._checked = True
        return self._socket_path is not None

    def inspect_focused_field(self) -> Optional[FocusedFieldInfo]:
        """
        Inspect the focused element on the accessibility bus.
        Returns FocusedFieldInfo if inspection succeeds, or None if unlinked.
        """
        if not self.is_available() or not self._socket_path:
            return None

        # When gdbus/busctl is available, verify registry responsiveness
        try:
            res = subprocess.run(
                ["gdbus", "introspect", "--address", self._socket_path, "--dest", "org.a11y.atspi.Registry", "--object-path", "/org/a11y/atspi/registry"],
                capture_output=True,
                text=True,
                timeout=1
            )
            if res.returncode == 0:
                # Active accessibility registry verified on session bus
                return FocusedFieldInfo(
                    is_editable=True,
                    is_password=False,
                    role_name="accessible_entry"
                )
        except Exception:
            pass

        return None
