import json
import shutil
import subprocess
from dataclasses import dataclass
from typing import Optional, Dict, Any

@dataclass
class WindowContext:
    app_class: str = ""
    title: str = ""
    pid: int = 0
    initial_title: str = ""
    app_category: str = "generic"  # "terminal", "code", "chat", "browser", "document", "generic"
    is_wayland: bool = True
    raw_data: Dict[str, Any] = None

def _categorize_app(app_class: str, title: str) -> str:
    cls = (app_class or "").lower()
    t = (title or "").lower()

    # Terminal emulators
    if any(term in cls for term in ("foot", "kitty", "alacritty", "wezterm", "gnome-terminal", "konsole", "xterm")):
        return "terminal"

    # Code editors & IDEs
    if any(ide in cls for ide in ("code", "cursor", "vscodium", "pycharm", "clion", "neovim", "emacs", "sublime", "antigravity", "zed", "fleet")):
        return "code"

    # Chat & messaging apps
    if any(chat in cls for chat in ("discord", "slack", "telegram", "element", "signal", "whatsapp", "teams")):
        return "chat"

    # Web browsers
    if any(browser in cls for browser in ("chrome", "chromium", "firefox", "brave", "zen", "vivaldi", "edge")):
        # Detect ChatGPT / Claude web tabs as chat
        if any(ai in t for ai in ("chatgpt", "claude", "gemini", "deepseek")):
            return "chat"
        return "browser"

    # Document & text editors
    if any(doc in cls for doc in ("libreoffice", "obsidian", "notion", "gedit", "kate", "xed")):
        return "document"

    return "generic"


def get_active_window() -> WindowContext:
    """
    Query active window metadata on Hyprland/Wayland via hyprctl.
    Falls back gracefully if not on Hyprland or hyprctl is unavailable.
    """
    if shutil.which("hyprctl"):
        try:
            res = subprocess.run(["hyprctl", "activewindow", "-j"], capture_output=True, text=True, timeout=1)
            if res.returncode == 0 and res.stdout.strip():
                data = json.loads(res.stdout)
                if isinstance(data, dict) and "class" in data:
                    app_class = data.get("class", "")
                    title = data.get("title", "")
                    pid = int(data.get("pid", 0))
                    initial_title = data.get("initialTitle", "")
                    category = _categorize_app(app_class, title)

                    return WindowContext(
                        app_class=app_class,
                        title=title,
                        pid=pid,
                        initial_title=initial_title,
                        app_category=category,
                        is_wayland=True,
                        raw_data=data
                    )
        except Exception:
            pass

    return WindowContext(
        app_class="unknown",
        title="unknown",
        pid=0,
        initial_title="unknown",
        app_category="generic",
        is_wayland=True,
        raw_data={}
    )
