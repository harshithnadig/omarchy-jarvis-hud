import re
from typing import Optional

class TextPolisher:
    """
    Intelligent Text Polisher & Normalizer.
    Phase 1: Safe deterministic sanitization (zero information loss).
    Phase 2: Local small LLM cleanup (Qwen2.5/3.5-2B) for conversational repair.
    """

    # Developer shorthand mappings (safe expansions)
    DEV_OPERATORS = {
        r"\b(?:fat arrow|fat error|fed arrow)\b": "=>",
        r"\b(?:skinny arrow|thin arrow)\b": "->",
        r"\b(?:triple equals|strict equals)\b": "===",
        r"\b(?:not equals|not equal to)\b": "!=",
        r"\b(?:pipe forward|pipeline operator)\b": "|>",
    }

    @classmethod
    def clean_deterministic(cls, text: str, dev_mode: bool = True) -> str:
        if not text:
            return ""

        # 1. Clean duplicated words/stutters (e.g. "the the" -> "the")
        cleaned = re.sub(r"\b([a-zA-Z]+)\s+\1\b", r"\1", text, flags=re.IGNORECASE)

        # 2. Clean verbal fillers
        cleaned = re.sub(r"\b(um|uh|erm|er|ah|ahh)\b", "", cleaned, flags=re.IGNORECASE)

        # 3. Collapse multiple spaces
        cleaned = re.sub(r"\s+", " ", cleaned).strip()

        # 4. Safe dev operators replacement if enabled
        if dev_mode:
            for pat, sym in cls.DEV_OPERATORS.items():
                cleaned = re.sub(pat, sym, cleaned, flags=re.IGNORECASE)

        # 5. Fix basic punctuation spacing
        cleaned = re.sub(r"\s+([,.?!;:])", r"\1", cleaned)

        # 6. Capitalize first letter
        if cleaned and cleaned[0].islower():
            cleaned = cleaned[0].upper() + cleaned[1:]

        return cleaned

    @classmethod
    def polish_with_llm(cls, raw_text: str, context: Optional[str] = None) -> str:
        """
        Hook for local Qwen3.5-2B / Qwen2.5-3B post-processor.
        Prompt rule: Preserve user meaning exactly. Fix speech artifacts only. Never add new facts.
        """
        # When Ollama or local LLM server is present, forward here.
        return cls.clean_deterministic(raw_text)
