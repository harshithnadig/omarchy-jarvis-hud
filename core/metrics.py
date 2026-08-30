import re
import math
from typing import List, Dict, Any, Optional

try:
    import jiwer
    HAS_JIWER = True
except ImportError:
    HAS_JIWER = False


def normalize_for_eval(text: str) -> str:
    """
    Standardizes text for fair ASR evaluation:
    - Lowercase
    - Strip punctuation
    - Collapse whitespace
    """
    if not text:
        return ""
    # Lowercase
    cleaned = text.lower()
    # Remove common punctuation
    cleaned = re.sub(r"[^\w\s]", "", cleaned)
    # Collapse multiple whitespaces
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned


def _levenshtein_distance(seq1: List[Any], seq2: List[Any]) -> int:
    """Pure-Python Levenshtein distance on arbitrary tokens/chars."""
    m, n = len(seq1), len(seq2)
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    for i in range(m + 1):
        dp[i][0] = i
    for j in range(n + 1):
        dp[0][j] = j
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if seq1[i - 1] == seq2[j - 1]:
                dp[i][j] = dp[i - 1][j - 1]
            else:
                dp[i][j] = 1 + min(dp[i - 1][j], dp[i][j - 1], dp[i - 1][j - 1])
    return dp[m][n]


def compute_wer(reference: str, hypothesis: str, normalize: bool = True) -> float:
    """
    Compute Word Error Rate (WER) between reference and hypothesis.
    Returns a float between 0.0 and infinity (usually <= 1.0).
    """
    ref = normalize_for_eval(reference) if normalize else reference.strip()
    hyp = normalize_for_eval(hypothesis) if normalize else hypothesis.strip()

    if not ref:
        return 0.0 if not hyp else 1.0

    if HAS_JIWER:
        try:
            return float(jiwer.wer(ref, hyp))
        except Exception:
            pass

    ref_words = ref.split()
    hyp_words = hyp.split()
    if not ref_words:
        return 0.0 if not hyp_words else 1.0

    distance = _levenshtein_distance(ref_words, hyp_words)
    return distance / len(ref_words)


def compute_cer(reference: str, hypothesis: str, normalize: bool = True) -> float:
    """
    Compute Character Error Rate (CER) between reference and hypothesis.
    """
    ref = normalize_for_eval(reference) if normalize else reference.strip()
    hyp = normalize_for_eval(hypothesis) if normalize else hypothesis.strip()

    if not ref:
        return 0.0 if not hyp else 1.0

    if HAS_JIWER:
        try:
            return float(jiwer.cer(ref, hyp))
        except Exception:
            pass

    ref_chars = list(ref.replace(" ", ""))
    hyp_chars = list(hyp.replace(" ", ""))
    if not ref_chars:
        return 0.0 if not hyp_chars else 1.0

    distance = _levenshtein_distance(ref_chars, hyp_chars)
    return distance / len(ref_chars)


def compute_summary_stats(values: List[float]) -> Dict[str, float]:
    """
    Compute comprehensive distribution statistics for a list of values.
    Returns count, min, max, mean, p50 (median), p90, p95, p99.
    """
    if not values:
        return {
            "count": 0,
            "min": 0.0,
            "max": 0.0,
            "mean": 0.0,
            "p50": 0.0,
            "p90": 0.0,
            "p95": 0.0,
            "p99": 0.0,
        }

    sorted_vals = sorted(values)
    n = len(sorted_vals)

    def percentile(p: float) -> float:
        if n == 1:
            return sorted_vals[0]
        k = (n - 1) * (p / 100.0)
        f = math.floor(k)
        c = math.ceil(k)
        if f == c:
            return sorted_vals[int(k)]
        d0 = sorted_vals[int(f)] * (c - k)
        d1 = sorted_vals[int(c)] * (k - f)
        return d0 + d1

    return {
        "count": n,
        "min": round(sorted_vals[0], 2),
        "max": round(sorted_vals[-1], 2),
        "mean": round(sum(sorted_vals) / n, 2),
        "p50": round(percentile(50), 2),
        "p90": round(percentile(90), 2),
        "p95": round(percentile(95), 2),
        "p99": round(percentile(99), 2),
    }
