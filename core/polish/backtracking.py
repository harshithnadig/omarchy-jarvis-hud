import re
from typing import Optional, List, Tuple

# Patterns for self-correction / backtracking cues
# Structure: (regex_pattern, replace_handler)
CORRECTION_PATTERNS = [
    # "scratch that, Y" -> replace preceding clause or phrase
    (r"(?:[,\s]+)?\b(?:scratch that|cancel that)\b[,\s]+(.*)$", r"\1"),
    # "X, actually Y" or "X... actually Y"
    (r"\b(\w+)[,.\s]+(?:actually|rather)[,.\s]+(\w+)\b", r"\2"),
    # "X, no, Y" / "X - no, Y" / "X, no Y"
    (r"\b(\w+)[,.\s—\-]+(?:no)[,.\s]+(\w+)\b", r"\2"),
    # "X, I mean Y" / "X I mean Y"
    (r"\b(\w+)[,.\s]+(?:i mean)[,.\s]+(\w+)\b", r"\2"),
]

class BacktrackingEngine:
    """
    Applies self-correction and verbal backtracking rules to transcripts.
    Corrects phrases like:
    - 'Book it for Tuesday... actually Wednesday.' -> 'Book it for Wednesday.'
    - 'Send it to Rahul - no, Rohan.' -> 'Send it to Rohan.'
    - 'We need Python, scratch that, Rust.' -> 'We need Rust.'
    """

    @classmethod
    def apply_backtracking(cls, text: str) -> str:
        if not text or not text.strip():
            return ""

        cleaned = text

        # 1. Handle explicit 'scratch that' / 'cancel that'
        # e.g., "Create a file named foo.py, scratch that, bar.py"
        m_scratch = re.search(r"^(.*?)(?:,\s*|\s+)\b(?:scratch that|cancel that)\b[,\s]*(.*)$", cleaned, flags=re.IGNORECASE)
        if m_scratch:
            pre_clause = m_scratch.group(1).strip()
            post_clause = m_scratch.group(2).strip()

            # If post_clause is a single token/replacement, find matching token in pre_clause
            post_words = post_clause.split()
            if len(post_words) == 1 and pre_clause:
                pre_words = pre_clause.split()
                # Replace the last word of pre_clause with post_clause
                pre_words[-1] = post_words[0]
                cleaned = " ".join(pre_words)
            else:
                # Replace the entire pre_clause if post_clause is a complete sentence or replace last clause
                cleaned = post_clause if len(post_words) > 3 else f"{pre_clause} {post_clause}"

        # 2. Handle "X actually Y", "X no, Y", "X I mean Y"
        # Match single-word substitutions: "Tuesday, actually Wednesday" -> "Wednesday"
        cleaned = re.sub(
            r"\b(\w+)[,.\s—\-]+(?:actually|rather)[,\s]+(\w+)\b",
            r"\2",
            cleaned,
            flags=re.IGNORECASE
        )

        # "X, no, Y" or "X - no, Y" (require comma or dash before 'no' and ensure word1 is not 'no')
        def replace_no_cue(m):
            w1 = m.group(1)
            w2 = m.group(2)
            if w1.lower() == "no" or w2.lower() == "no":
                return m.group(0)  # Preserve "no no"
            return w2

        cleaned = re.sub(
            r"\b(\w+)[,\s—\-]+(?:no)[,\s]+(\w+)\b",
            replace_no_cue,
            cleaned,
            flags=re.IGNORECASE
        )

        cleaned = re.sub(
            r"\b(\w+)[,.\s—\-]+(?:i mean)[,\s]+(\w+)\b",
            r"\2",
            cleaned,
            flags=re.IGNORECASE
        )

        # Cleanup whitespace
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        return cleaned
