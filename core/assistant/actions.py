import re
import time
import subprocess
import urllib.request
import urllib.parse
from enum import Enum
from typing import Optional, Tuple

class PermissionClass(Enum):
    SAFE = "SAFE"
    SENSITIVE = "SENSITIVE"
    DESTRUCTIVE = "DESTRUCTIVE"

class LocalActionExecutor:
    """
    Fast-path local actions (< 50ms) for common desktop commands.
    """

    @classmethod
    def match_and_execute(cls, query: str) -> Optional[Tuple[str, PermissionClass]]:
        q = query.lower().strip()
        # Clean optional greeting/wake prefix
        q = re.sub(r"^(?:hey\s+|ok\s+|yo\s+|hello\s+)?ja[rn]?v[ie][scz][,:\s]*", "", q).strip()

        # Greetings & Status
        if q in ["hey", "hello", "hi", "how are you", "who are you"]:
            return ("Hello! JARVIS online and ready. What can I do for you?", PermissionClass.SAFE)

        # Date & Day
        if "date" in q or "today's date" in q or "what day is it" in q or q in ["today", "day"]:
            return (time.strftime("Today is %A, %B %d, %Y."), PermissionClass.SAFE)

        # Current Time
        if "what time is it" in q or "current time" in q or "what's the time" in q or q == "time":
            return (time.strftime("It is currently %I:%M %p."), PermissionClass.SAFE)

        # Battery / Power
        if "battery" in q or "power level" in q:
            try:
                with open("/sys/class/power_supply/BAT0/capacity") as f:
                    cap = f.read().strip()
                with open("/sys/class/power_supply/BAT0/status") as f:
                    stat = f.read().strip()
                return (f"Battery is at {cap}% and currently {stat}.", PermissionClass.SAFE)
            except Exception:
                pass

        # Weather query (wttr.in)
        if "weather" in q:
            city = "Bangalore"
            m = re.search(r"weather (?:in|for|at)?\s*([a-zA-Z\s]+)", q)
            if m and m.group(1).strip() and m.group(1).strip() not in ["today", "now", "outside", "like"]:
                city = m.group(1).strip().replace(" today", "").replace(" now", "").strip()
            try:
                req = urllib.request.Request(f"https://wttr.in/{urllib.parse.quote(city)}?format=%C,+%t", headers={"User-Agent": "curl/8.0"})
                with urllib.request.urlopen(req, timeout=2) as resp:
                    w_text = resp.read().decode().strip()
                    if w_text:
                        return (f"In {city.title()}, the weather is currently {w_text}.", PermissionClass.SAFE)
            except Exception:
                pass

        # System Controls
        if "lock screen" in q or "lock the screen" in q or "lock my laptop" in q:
            subprocess.Popen(["omarchy", "system", "lock"])
            return ("Locking your screen.", PermissionClass.SAFE)

        if "open browser" in q or "launch browser" in q or "open chrome" in q:
            subprocess.Popen(["google-chrome-stable"])
            return ("Opening Google Chrome.", PermissionClass.SAFE)

        if "open terminal" in q or "launch terminal" in q:
            subprocess.Popen(["foot"])
            return ("Opening terminal.", PermissionClass.SAFE)

        if "open code" in q or "open vs code" in q or "open vscode" in q:
            subprocess.Popen(["code"])
            return ("Opening VS Code.", PermissionClass.SAFE)

        if "volume up" in q or "increase volume" in q:
            subprocess.run(["wpctl", "set-volume", "@DEFAULT_AUDIO_SINK@", "5%+"], check=False)
            return ("Volume increased.", PermissionClass.SAFE)

        if "volume down" in q or "decrease volume" in q:
            subprocess.run(["wpctl", "set-volume", "@DEFAULT_AUDIO_SINK@", "5%-"], check=False)
            return ("Volume decreased.", PermissionClass.SAFE)

        if "mute" in q or "unmute" in q:
            subprocess.run(["wpctl", "set-mute", "@DEFAULT_AUDIO_SINK@", "toggle"], check=False)
            return ("Audio toggled.", PermissionClass.SAFE)

        return None
