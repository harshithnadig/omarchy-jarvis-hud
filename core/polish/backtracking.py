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

PREPOSITIONS = {'for', 'to', 'at', 'on', 'in', 'named', 'called', 'with', 'from', 'as', 'method', 'function', 'variable', 'const', 'let'}

NON_CORRECTION_NO_WORDS = {'problem', 'way', 'doubt', 'idea', 'worries', 'longer', 'matter', 'more', 'less', 'one', 'body', 'thanks'}

class BacktrackingEngine:
    """
    Applies self-correction and verbal backtracking rules to transcripts.
    Handles single tokens, multi-word clauses, and preposition-anchored corrections:
    - 'Schedule the deployment for Tuesday actually Wednesday morning.' -> 'Schedule the deployment for Wednesday morning.'
    - 'Let us name the method get_user_data, I mean fetch_user_data.' -> 'Let us name the method fetch_user_data.'
    - 'Send it to Rahul no Rohan.' -> 'Send it to Rohan.'
    - 'We need Python, scratch that, Rust.' -> 'We need Rust.'
    """

    @classmethod
    def apply_backtracking(cls, text: str) -> str:
        if not text or not text.strip():
            return ""

        cleaned = text.strip()

        # 1. Handle explicit 'scratch that' / 'cancel that'
        m_scratch = re.search(r"^(.*?)(?:,\s*|\s+)\b(?:scratch that|cancel that)\b[,\s]*(.*)$", cleaned, flags=re.IGNORECASE)
        if m_scratch:
            pre = m_scratch.group(1).strip()
            post = m_scratch.group(2).strip()
            if not pre:
                return post
            post_words = post.split()
            pre_words = pre.split()
            if len(post_words) == 1 and pre_words:
                pre_words[-1] = post_words[0]
                return " ".join(pre_words)
            return post if len(post_words) > 3 else f"{pre} {post}"

        # 2. Cues: 'I mean', 'actually', 'rather', 'no'
        cue_match = re.search(r"[,.\s—\-]+(?:\b(?:i mean|actually|rather|no)\b)[,\s]*", cleaned, flags=re.IGNORECASE)
        if not cue_match:
            return cleaned

        idx = cue_match.start()
        end_idx = cue_match.end()

        pre = cleaned[:idx].rstrip(",.-— ")
        post = cleaned[end_idx:].lstrip(",.-— ")

        pre_words = pre.split()
        post_words = post.split()

        if not pre_words or not post_words:
            return cleaned

        # Avoid triggering on intentional 'no no' or idioms like 'no problem'
        if post_words[0].lower() in NON_CORRECTION_NO_WORDS:
            return cleaned
        if pre_words[-1].lower() == "no":
            return cleaned

        # Check if there is a preposition or anchor noun in the last few words of pre
        for i in range(len(pre_words) - 1, max(-1, len(pre_words) - 5), -1):
            if pre_words[i].lower() in PREPOSITIONS and (not post_words or post_words[0].lower() not in PREPOSITIONS):
                result = " ".join(pre_words[:i+1]) + " " + post
                return re.sub(r"\s+", " ", result).strip()

        # Default fallback: replace last min(len(post_words), len(pre_words)) words
        n = min(len(post_words), len(pre_words))
        result = " ".join(pre_words[:-n]) + " " + post
        return re.sub(r"\s+", " ", result).strip()
