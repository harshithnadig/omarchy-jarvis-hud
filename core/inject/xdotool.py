import shutil
import subprocess
from .base import TextInjector, TextInjectionError

class XdotoolInjector(TextInjector):
    """
    X11 / XWayland text injector using xdotool.
    """
    def __init__(self, key_delay_ms: int = 0):
        super().__init__(name="xdotool")
        self.key_delay_ms = key_delay_ms

    def is_available(self) -> bool:
        return shutil.which("xdotool") is not None

    def inject(self, text: str) -> bool:
        if not text:
            return True
        if not self.is_available():
            raise TextInjectionError("xdotool is not installed on the system.")

        cmd = ["xdotool", "type", "--clearmodifiers"]
        if self.key_delay_ms > 0:
            cmd.extend(["--delay", str(self.key_delay_ms)])
        cmd.extend(["--", text])

        try:
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            if res.returncode != 0:
                raise TextInjectionError(f"xdotool failed: {res.stderr.strip()}")
            return True
        except Exception as e:
            raise TextInjectionError(f"xdotool execution error: {e}") from e
