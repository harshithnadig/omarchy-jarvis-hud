import re
from typing import Optional, Set
from .polish.backtracking import BacktrackingEngine
from .polish.developer import DeveloperTransformEngine
from .context.profiles import StyleProfile, PROFILES

class TextPolisher:
    """
    Intelligent Deterministic Text Polisher & Normalizer (Phase 5).
    - Preserves exact user intent while removing acoustic artifacts and stutters.
    - Handles backtracking ("X... actually Y", "X - no, Y", "scratch that").
    - Expands developer syntax (camelCase, snake_case, PascalCase, code operators).
    - Adapts formatting based on active application style profile.
    """

    # Intentional repetitions that should NOT be collapsed as stutters
    PRESERVED_REPETITIONS: Set[str] = {
        "very", "really", "had", "that", "no", "so", "bye", "knock", "much", "far", "never", "now", "again"
    }

    # Common verbal hesitation filler tokens
    FILLER_WORDS = r"\b(?:um|uh|erm|er|ah|ahh)\b"

    @classmethod
    def _deduplicate_stutters(cls, text: str) -> str:
        """Collapse stuttered repeated words unless they are intentional intensifiers."""
        def replace_dup(match):
            word = match.group(1)
            if word.lower() in cls.PRESERVED_REPETITIONS:
                return match.group(0)  # Preserve e.g. "very very"
            return word

        # Match adjacent identical whole words (case-insensitive)
        return re.sub(r"\b([a-zA-Z]+)\s+\1\b", replace_dup, text, flags=re.IGNORECASE)

    @classmethod
    def clean_deterministic(
        cls,
        text: str,
        dev_mode: bool = True,
        enable_backtracking: bool = True,
        profile: Optional[StyleProfile] = None
    ) -> str:
        if not text or not text.strip():
            return ""

        prof = profile or PROFILES["generic"]
        cleaned = text.strip()

        # 1. Clean verbal fillers
        cleaned = re.sub(cls.FILLER_WORDS, "", cleaned, flags=re.IGNORECASE)

        # 2. Collapse stuttered duplicated words (preserving intentional repetitions)
        cleaned = cls._deduplicate_stutters(cleaned)

        # 3. Apply self-correction & verbal backtracking ("X... actually Y")
        if enable_backtracking:
            cleaned = BacktrackingEngine.apply_backtracking(cleaned)

        # 4. Fix punctuation spacing and orphan punctuation
        if prof.auto_punctuate:
            cleaned = re.sub(r"\s+([,.?!;:])", r"\1", cleaned)
            cleaned = re.sub(r"([,;:])\s*[,;:]+", r"\1", cleaned)
            cleaned = re.sub(r"^\s*[,;:]\s*", "", cleaned)

        # 5. Developer transforms (operators, punctuation symbols, casing commands)
        if dev_mode or prof.enable_dev_operators or prof.enable_casing_transforms:
            cleaned = DeveloperTransformEngine.apply_dev_transforms(
                cleaned,
                enable_casing=prof.enable_casing_transforms or dev_mode
            )

        # 6. Collapse multiple spaces
        cleaned = re.sub(r"\s+", " ", cleaned).strip()

        # 7. Strip trailing period if requested by profile (e.g. terminal profile)
        if prof.strip_trailing_period and cleaned.endswith("."):
            cleaned = cleaned[:-1].rstrip()

        # 8. Leading character capitalization based on style profile
        if prof.auto_capitalize and cleaned and cleaned[0].isalpha() and cleaned[0].islower():
            cleaned = cleaned[0].upper() + cleaned[1:]

        return cleaned

    @classmethod
    def polish_with_llm(cls, raw_text: str, context: Optional[str] = None) -> str:
        """
        Hook for local Qwen / small LLM post-processor (Phase 8).
        Falls back to safe deterministic cleanup.
        """
        from .polish.llm import LocalLLMPolisher
        return LocalLLMPolisher.polish(raw_text, context=context)

