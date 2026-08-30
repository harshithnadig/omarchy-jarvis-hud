import re
from typing import Optional, Set

class TextPolisher:
    """
    Deterministic Text Polisher & Normalizer.
    Phase 1: Safe deterministic sanitization (zero information loss).
    Phase 5 / Phase 8: Advanced self-correction and optional local LLM post-processing.
    """

    # Developer shorthand mappings (safe expansions in dev mode)
    DEV_OPERATORS = {
        r"\b(?:fat arrow|fat error|fed arrow)\b": "=>",
        r"\b(?:skinny arrow|thin arrow)\b": "->",
        r"\b(?:triple equals|strict equals)\b": "===",
        r"\b(?:not equals|not equal to)\b": "!=",
        r"\b(?:pipe forward|pipeline operator)\b": "|>",
        r"\b(?:optional chaining|optional chain)\b": "?.",
        r"\b(?:nullish coalescing|double question mark)\b": "??",
        r"\b(?:logical and|double ampersand)\b": "&&",
        r"\b(?:logical or|double pipe)\b": "||",
    }

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
    def clean_deterministic(cls, text: str, dev_mode: bool = True) -> str:
        if not text or not text.strip():
            return ""

        cleaned = text.strip()

        # 1. Clean verbal fillers
        cleaned = re.sub(cls.FILLER_WORDS, "", cleaned, flags=re.IGNORECASE)

        # 2. Collapse stuttered duplicated words (preserving intentional repetitions)
        cleaned = cls._deduplicate_stutters(cleaned)

        # 3. Fix punctuation spacing and orphan punctuation
        # Remove space before punctuation: "word ," -> "word,"
        cleaned = re.sub(r"\s+([,.?!;:])", r"\1", cleaned)
        # Collapse multiple adjacent commas or duplicate punctuation: ", ," -> ","
        cleaned = re.sub(r"([,;:])\s*[,;:]+", r"\1", cleaned)
        # Remove leading punctuation resulting from filler removal at start: ", Hello" -> "Hello"
        cleaned = re.sub(r"^\s*[,;:]\s*", "", cleaned)

        # 4. Safe dev operators replacement if enabled
        if dev_mode:
            for pat, sym in cls.DEV_OPERATORS.items():
                cleaned = re.sub(pat, sym, cleaned, flags=re.IGNORECASE)

        # 5. Collapse multiple spaces
        cleaned = re.sub(r"\s+", " ", cleaned).strip()

        # 6. Ensure leading character capitalization if alphanumeric
        if cleaned and cleaned[0].isalpha() and cleaned[0].islower():
            cleaned = cleaned[0].upper() + cleaned[1:]

        return cleaned

    @classmethod
    def polish_with_llm(cls, raw_text: str, context: Optional[str] = None) -> str:
        """
        Placeholder hook for optional local LLM post-processor (Phase 8).
        Currently falls back to safe deterministic cleanup.
        """
        return cls.clean_deterministic(raw_text)
