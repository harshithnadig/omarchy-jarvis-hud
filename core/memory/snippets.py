import os
import re
import json
from typing import Dict, Optional

DEFAULT_SNIPPETS_PATH = os.path.expanduser("~/.local/share/jarvis-voice/snippets.json")

BUILTIN_SNIPPETS = {
    "insert bug template": "### Bug Description\n\n**Steps to Reproduce:**\n1. \n\n**Expected Behavior:**\n\n**Actual Behavior:**",
    "insert pr template": "## Summary\n\n## Changes\n- \n\n## Test Plan\n- ",
    "insert github signature": "\n\n---\n*Authored via JARVIS Voice on Omarchy Linux*",
}

class SnippetManager:
    """
    Manages custom voice text snippets and expansion templates.
    """
    def __init__(self, snippets_path: Optional[str] = None):
        self.snippets_path = snippets_path or DEFAULT_SNIPPETS_PATH
        os.makedirs(os.path.dirname(os.path.abspath(self.snippets_path)), exist_ok=True)
        self.snippets = self._load_snippets()

    def _load_snippets(self) -> Dict[str, str]:
        if os.path.exists(self.snippets_path):
            try:
                with open(self.snippets_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass

        # Initialize with builtins
        self.save_snippets(BUILTIN_SNIPPETS)
        return dict(BUILTIN_SNIPPETS)

    def save_snippets(self, data: Dict[str, str]):
        with open(self.snippets_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def add_snippet(self, voice_trigger: str, expansion_text: str):
        self.snippets[voice_trigger.lower().strip()] = expansion_text
        self.save_snippets(self.snippets)

    def expand_snippets(self, text: str) -> str:
        if not text:
            return ""

        cleaned = text.strip()
        # Direct exact match or prefix match for voice snippet commands
        for trigger, expansion in self.snippets.items():
            pattern = r"^\s*" + re.escape(trigger) + r"\s*$"
            if re.match(pattern, cleaned, flags=re.IGNORECASE):
                return expansion

        return text
