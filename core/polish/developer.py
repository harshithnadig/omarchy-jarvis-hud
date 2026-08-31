import re
from typing import List

class DeveloperTransformEngine:
    """
    Transforms spoken developer syntax into actual identifiers and code operators.
    """

    OPERATORS = {
        r"\b(?:fat arrow|fat error|fed arrow)\b": "=>",
        r"\b(?:skinny arrow|thin arrow)\b": "->",
        r"\b(?:triple equals|strict equals)\b": "===",
        r"\b(?:not equals|not equal to)\b": "!=",
        r"\b(?:pipe forward|pipeline operator)\b": "|>",
        r"\b(?:optional chaining|optional chain)\b": "?.",
        r"\b(?:nullish coalescing|double question mark)\b": "??",
        r"\b(?:logical and|double ampersand)\b": "&&",
        r"\b(?:logical or|double pipe)\b": "||",
        r"\b(?:plus equals|increment by)\b": "+=",
        r"\b(?:minus equals|decrement by)\b": "-=",
        r"\b(?:times equals|multiply by)\b": "*=",
        r"\b(?:divide equals)\b": "/=",
    }

    KEYWORDS = {
        r"\b(?:use state)\b": "useState",
        r"\b(?:use effect)\b": "useEffect",
        r"\b(?:use ref)\b": "useRef",
        r"\b(?:use callback)\b": "useCallback",
        r"\b(?:use memo)\b": "useMemo",
        r"\b(?:use context)\b": "useContext",
        r"\b(?:console dot log|console log)\b": "console.log",
        r"\b(?:print line|println)\b": "println",
    }

    PUNCTUATION_SYMBOLS = {
        r"\b(?:open paren|open parenthesis|left paren)\b": "(",
        r"\b(?:close paren|close parenthesis|right paren)\b": ")",
        r"\b(?:open bracket|left bracket|open square bracket)\b": "[",
        r"\b(?:close bracket|right bracket|close square bracket)\b": "]",
        r"\b(?:open brace|open curly brace|left brace)\b": "{",
        r"\b(?:close brace|close curly brace|right brace)\b": "}",
        r"\b(?:semicolon)\b": ";",
        r"\b(?:backtick|backticks)\b": "`",
        r"\b(?:double quotes|double quote)\b": '"',
        r"\b(?:single quote)\b": "'",
        r"\b(?<=[a-zA-Z0-9_])\s+dot\s+(?=[a-zA-Z0-9_])\b": ".",
    }

    @staticmethod
    def _to_camel_case(words: List[str]) -> str:
        if not words:
            return ""
        return words[0].lower() + "".join(w.capitalize() for w in words[1:])

    @staticmethod
    def _to_snake_case(words: List[str]) -> str:
        return "_".join(w.lower() for w in words)

    @staticmethod
    def _to_pascal_case(words: List[str]) -> str:
        return "".join(w.capitalize() for w in words)

    @staticmethod
    def _to_kebab_case(words: List[str]) -> str:
        return "-".join(w.lower() for w in words)

    @staticmethod
    def _to_screaming_snake_case(words: List[str]) -> str:
        return "_".join(w.upper() for w in words)

    @classmethod
    def apply_casing_transforms(cls, text: str) -> str:
        """
        Detects casing commands like:
        - "camel case user profile picture" -> "userProfilePicture"
        - "snake case user profile picture" -> "user_profile_picture"
        - "pascal case user profile picture" -> "UserProfilePicture"
        - "kebab case user profile picture" -> "user-profile-picture"
        - "screaming snake case max retries" -> "MAX_RETRIES"
        """
        # 1. Screaming snake case / Constant case (Must precede snake case)
        def replace_screaming(m):
            words = m.group(1).strip().split()
            return cls._to_screaming_snake_case(words)

        text = re.sub(r"\b(?:screaming snake case|constant case)\s+([a-zA-Z0-9\s]+?)(?=\s+(?:and|or|is|in|to|with|for|=>|===|!=|\.|\,|$)|$)", replace_screaming, text, flags=re.IGNORECASE)

        # 2. Camel case
        def replace_camel(m):
            words = m.group(1).strip().split()
            return cls._to_camel_case(words)

        text = re.sub(r"\b(?:camel case|camelcase)\s+([a-zA-Z0-9\s]+?)(?=\s+(?:and|or|is|in|to|with|for|=>|===|!=|\.|\,|$)|$)", replace_camel, text, flags=re.IGNORECASE)

        # 3. Snake case
        def replace_snake(m):
            words = m.group(1).strip().split()
            return cls._to_snake_case(words)

        text = re.sub(r"\b(?:snake case|snakecase)\s+([a-zA-Z0-9\s]+?)(?=\s+(?:and|or|is|in|to|with|for|=>|===|!=|\.|\,|$)|$)", replace_snake, text, flags=re.IGNORECASE)

        # 4. Pascal case
        def replace_pascal(m):
            words = m.group(1).strip().split()
            return cls._to_pascal_case(words)

        text = re.sub(r"\b(?:pascal case|pascalcase)\s+([a-zA-Z0-9\s]+?)(?=\s+(?:and|or|is|in|to|with|for|=>|===|!=|\.|\,|$)|$)", replace_pascal, text, flags=re.IGNORECASE)

        # 5. Kebab case
        def replace_kebab(m):
            words = m.group(1).strip().split()
            return cls._to_kebab_case(words)

        text = re.sub(r"\b(?:kebab case|kebabcase)\s+([a-zA-Z0-9\s]+?)(?=\s+(?:and|or|is|in|to|with|for|=>|===|!=|\.|\,|$)|$)", replace_kebab, text, flags=re.IGNORECASE)

        return text

    @classmethod
    def apply_dev_transforms(cls, text: str, enable_casing: bool = True) -> str:
        if not text or not text.strip():
            return ""

        cleaned = text

        # 1. Operators
        for pat, sym in cls.OPERATORS.items():
            cleaned = re.sub(pat, sym, cleaned, flags=re.IGNORECASE)

        # 2. Keywords
        for pat, kw in cls.KEYWORDS.items():
            cleaned = re.sub(pat, kw, cleaned, flags=re.IGNORECASE)

        # 3. Spoken symbols
        for pat, sym in cls.PUNCTUATION_SYMBOLS.items():
            cleaned = re.sub(pat, sym, cleaned, flags=re.IGNORECASE)

        # 4. Casing transforms
        if enable_casing:
            cleaned = cls.apply_casing_transforms(cleaned)

        return cleaned
