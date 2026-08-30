import shutil
import subprocess
from .base import TextInjector, TextInjectionError

class WtypeInjector(TextInjector):
    """
    Wayland direct keystroke typing injector using wtype.
    Works on wlroots/Hyprland compositors.
    """
    def __init__(self, delay_ms: int = 0):
        super().__init__(name="wtype")
        self.delay_ms = delay_ms

    def is_available(self) -> bool:
        return shutil.which("wtype") is not None

    def inject(self, text: str) -> bool:
        if not text:
            return True
        if not self.is_available():
            raise TextInjectionError("wtype is not installed on the system.")

        cmd = ["wtype"]
        if self.delay_ms > 0:
            cmd.extend(["-s", str(self.delay_ms)])
        cmd.extend(["--", text])

        try:
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            if res.returncode != 0:
                raise TextInjectionError(f"wtype failed with code {res.returncode}: {res.stderr.strip()}")
            return True
        except subprocess.TimeoutExpired as e:
            raise TextInjectionError("wtype timed out during typing.") from e
        except Exception as e:
            raise TextInjectionError(f"wtype execution error: {e}") from e
