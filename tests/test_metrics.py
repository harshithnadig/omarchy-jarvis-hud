import pytest
from core.metrics import (
    normalize_for_eval,
    compute_wer,
    compute_cer,
    compute_summary_stats,
)

def test_normalize_for_eval():
    assert normalize_for_eval("Hello, World! 123") == "hello world 123"
    assert normalize_for_eval("  multiple   spaces \n and tabs  ") == "multiple spaces and tabs"
    assert normalize_for_eval("") == ""

def test_compute_wer_exact():
    ref = "the quick brown fox jumps over the lazy dog"
    hyp = "the quick brown fox jumps over the lazy dog"
    assert compute_wer(ref, hyp) == 0.0

def test_compute_wer_substitutions_and_deletions():
    ref = "the quick brown fox"
    hyp = "the fast brown"  # 1 substitution (quick->fast), 1 deletion (fox)
    wer = compute_wer(ref, hyp)
    assert wer == 0.5  # 2 errors / 4 words = 0.5

def test_compute_wer_empty():
    assert compute_wer("", "") == 0.0
    assert compute_wer("hello", "") == 1.0
    assert compute_wer("", "hello") == 1.0

def test_compute_cer():
    ref = "cat"
    hyp = "car"
    assert compute_cer(ref, hyp) == pytest.approx(1.0 / 3.0, 0.01)

def test_compute_summary_stats():
    values = [10.0, 20.0, 30.0, 40.0, 50.0, 60.0, 70.0, 80.0, 90.0, 100.0]
    stats = compute_summary_stats(values)
    assert stats["count"] == 10
    assert stats["min"] == 10.0
    assert stats["max"] == 100.0
    assert stats["mean"] == 55.0
    assert stats["p50"] == 55.0
    assert stats["p95"] == pytest.approx(95.5, 0.5)

def test_compute_summary_stats_empty():
    stats = compute_summary_stats([])
    assert stats["count"] == 0
    assert stats["mean"] == 0.0
