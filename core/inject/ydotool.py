import shutil
import subprocess
from .base import TextInjector, TextInjectionError

class YdotoolInjector(TextInjector):
    """
    Uinput-based text injection via ydotool.
    Works on all Wayland compositors (Hyprland, Sway, GNOME, KDE) with ydotoold daemon running.
    """
    def __init__(self, key_delay_ms: int = 0):
        super().__init__(name="ydotool")
        self.key_delay_ms = key_delay_ms

    def is_available(self) -> bool:
        return shutil.which("ydotool") is not None

    def inject(self, text: str) -> bool:
        if not text:
            return True
        if not self.is_available():
            raise TextInjectionError("ydotool is not installed on the system.")

        cmd = ["ydotool", "type"]
        if self.key_delay_ms > 0:
            cmd.extend(["-d", str(self.key_delay_ms)])
        cmd.extend(["--", text])

        try:
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            if res.returncode != 0:
                raise TextInjectionError(f"ydotool failed: {res.stderr.strip()}")
            return True
        except Exception as e:
            raise TextInjectionError(f"ydotool execution error: {e}") from e
