import re
from typing import Optional
from .active_window import WindowContext

# Regex patterns for sensitive windows where context tracking/logging should be inhibited
SENSITIVE_WINDOW_PATTERNS = [
    r"\b(?:password|passwords|bitwarden|1password|keepass|keepassxc|lastpass|auth|authenticator|login|signin|sign in|vault)\b",
    r"\b(?:sudo|pkexec|gcr-prompter|polkit|pinentry|ssh-askpass|credentials)\b",
    r"\b(?:banking|bank|checkout|credit card|cvv)\b",
]

class PrivacyEngine:
    """
    Manages privacy protection, sensitive input masking, and global Private Mode.
    """
    def __init__(self, private_mode: bool = False):
        self.private_mode = private_mode

    def is_sensitive(self, context: Optional[WindowContext]) -> bool:
        """Check if active window corresponds to a sensitive credential or banking input."""
        if not context:
            return False

        search_text = f"{context.app_class} {context.title} {context.initial_title}".lower()

        for pat in SENSITIVE_WINDOW_PATTERNS:
            if re.search(pat, search_text, flags=re.IGNORECASE):
                return True
        return False

    def should_capture_context(self, context: Optional[WindowContext]) -> bool:
        """Determine if context collection is permitted."""
        if self.private_mode:
            return False
        if self.is_sensitive(context):
            return False
        return True

    def should_persist_history(self, context: Optional[WindowContext]) -> bool:
        """Determine if transcripts may be written to disk/history."""
        if self.private_mode:
            return False
        if self.is_sensitive(context):
            return False
        return True
