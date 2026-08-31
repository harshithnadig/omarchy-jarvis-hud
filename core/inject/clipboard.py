import time
import shutil
import subprocess
from typing import Optional
from .base import TextInjector, TextInjectionError

class SafeClipboardInjector(TextInjector):
    """
    Wayland Safe Clipboard Injector using wl-copy/wl-paste + wtype.
    Saves the user's previous clipboard content, pastes text, and restores clipboard.
    """
    def __init__(self, restore_delay_ms: int = 150):
        super().__init__(name="safe-clipboard")
        self.restore_delay_ms = restore_delay_ms

    def is_available(self) -> bool:
        return (
            shutil.which("wl-copy") is not None
            and shutil.which("wl-paste") is not None
            and shutil.which("wtype") is not None
        )

    def _get_current_clipboard(self) -> Optional[str]:
        try:
            res = subprocess.run(["wl-paste", "--no-newline"], capture_output=True, text=True, timeout=1)
            if res.returncode == 0:
                return res.stdout
        except Exception:
            pass
        return None

    def _set_clipboard(self, text: str):
        try:
            subprocess.run(["wl-copy"], input=text, text=True, check=True, timeout=1)
        except Exception as e:
            raise TextInjectionError(f"Failed to copy to clipboard via wl-copy: {e}") from e

    def _send_paste_keystroke(self, shortcut: str = "ctrl+v"):
        try:
            if shortcut.lower() == "ctrl+shift+v":
                subprocess.run(["wtype", "-M", "ctrl", "-M", "shift", "-P", "v", "-m", "shift", "-m", "ctrl"], check=True, timeout=1)
            else:
                # Standard Ctrl+V
                subprocess.run(["wtype", "-M", "ctrl", "-P", "v", "-m", "ctrl"], check=True, timeout=1)
        except Exception as e:
            raise TextInjectionError(f"Failed to send paste keystroke ({shortcut}) via wtype: {e}") from e

    def inject(self, text: str, paste_shortcut: str = "ctrl+v") -> bool:
        if not text:
            return True
        if not self.is_available():
            raise TextInjectionError("wl-copy, wl-paste, or wtype not available for clipboard injection.")

        previous_clipboard = self._get_current_clipboard()

        try:
            # 1. Put dictation text on clipboard
            self._set_clipboard(text)

            # 2. Trigger paste in active window
            self._send_paste_keystroke(shortcut=paste_shortcut)

            # 3. Allow target application window a brief window to receive paste event
            if self.restore_delay_ms > 0:
                time.sleep(self.restore_delay_ms / 1000.0)

            return True
        finally:
            # 4. Restore original clipboard content so user's clipboard is preserved
            if previous_clipboard is not None:
                try:
                    self._set_clipboard(previous_clipboard)
                except Exception:
                    pass
