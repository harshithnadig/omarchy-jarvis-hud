import os
import re
import sqlite3
from typing import Optional, Dict, List, Tuple

DEFAULT_DB_PATH = os.path.expanduser("~/.local/share/jarvis-voice/dictionary.db")

BUILTIN_TERMS = [
    ("hyprland", "Hyprland", "global"),
    ("hyper land", "Hyprland", "global"),
    ("hyperland", "Hyprland", "global"),
    ("omarchy", "Omarchy", "global"),
    ("fastapi", "FastAPI", "global"),
    ("fast api", "FastAPI", "global"),
    ("ctranslate", "CTranslate2", "global"),
    ("ctranslate2", "CTranslate2", "global"),
    ("see translate", "CTranslate2", "global"),
    ("wispr", "Wispr", "global"),
    ("whispr", "Wispr", "global"),
    ("silero", "Silero", "global"),
    ("solero", "Silero", "global"),
    ("vram", "VRAM", "global"),
    ("v ram", "VRAM", "global"),
    ("rtx", "RTX", "global"),
    ("nemo", "NeMo", "global"),
    ("wayland", "Wayland", "global"),
    ("pipewire", "PipeWire", "global"),
    ("quickshell", "Quickshell", "global"),
    ("antigravity", "Antigravity", "global"),
]

class PersonalDictionary:
    """
    Local SQLite-backed personal dictionary for domain terms and technical acronyms.
    """
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or DEFAULT_DB_PATH
        os.makedirs(os.path.dirname(os.path.abspath(self.db_path)), exist_ok=True)
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        with self._get_conn() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS dictionary (
                    spoken_form TEXT PRIMARY KEY,
                    canonical_form TEXT NOT NULL,
                    app_scope TEXT DEFAULT 'global',
                    frequency INTEGER DEFAULT 1,
                    last_used_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            # Seed built-in terms if empty
            cur = conn.execute("SELECT COUNT(*) FROM dictionary")
            if cur.fetchone()[0] == 0:
                for spoken, canonical, scope in BUILTIN_TERMS:
                    conn.execute(
                        "INSERT OR IGNORE INTO dictionary (spoken_form, canonical_form, app_scope) VALUES (?, ?, ?)",
                        (spoken.lower(), canonical, scope)
                    )
            conn.commit()

    def add_entry(self, spoken_form: str, canonical_form: str, app_scope: str = "global"):
        with self._get_conn() as conn:
            conn.execute(
                """
                INSERT INTO dictionary (spoken_form, canonical_form, app_scope, frequency)
                VALUES (?, ?, ?, 1)
                ON CONFLICT(spoken_form) DO UPDATE SET
                    canonical_form=excluded.canonical_form,
                    app_scope=excluded.app_scope,
                    frequency=frequency + 1,
                    last_used_at=CURRENT_TIMESTAMP
                """,
                (spoken_form.lower().strip(), canonical_form.strip(), app_scope.strip())
            )
            conn.commit()

    def get_entries(self, app_class: Optional[str] = None) -> List[Tuple[str, str]]:
        """Retrieve active dictionary rules sorted by longest spoken string first."""
        with self._get_conn() as conn:
            cur = conn.execute("SELECT spoken_form, canonical_form, app_scope FROM dictionary")
            rows = cur.fetchall()

        matched = []
        for spoken, canonical, scope in rows:
            if scope == "global" or (app_class and scope.lower() == app_class.lower()):
                matched.append((spoken, canonical))

        # Sort by length descending so longer multi-word phrases match before single words
        matched.sort(key=lambda x: len(x[0]), reverse=True)
        return matched

    def apply_dictionary(self, text: str, app_class: Optional[str] = None) -> str:
        if not text or not text.strip():
            return ""

        entries = self.get_entries(app_class=app_class)
        result = text

        for spoken, canonical in entries:
            # Whole-word regex replacement
            pattern = r"\b" + re.escape(spoken) + r"\b"
            result = re.sub(pattern, canonical, result, flags=re.IGNORECASE)

        return result
