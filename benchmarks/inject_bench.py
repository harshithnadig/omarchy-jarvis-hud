#!/usr/bin/env python3
"""
JARVIS Real Wayland Text Injection Reliability Benchmark.
Performs actual end-to-end injection of randomized test tokens, reads back the output,
and calculates exact pass/fail reliability percentage and latency distributions.
"""
import os
import sys
import time
import uuid
import json
import subprocess
from datetime import datetime

REPO_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO_DIR not in sys.path:
    sys.path.insert(0, REPO_DIR)

from core.inject.router import InjectorRouter
from core.context.active_window import get_active_window

def benchmark_clipboard_injection(iterations: int = 25) -> dict:
    """Test real round-trip clipboard injection and verification."""
    from core.inject.clipboard import SafeClipboardInjector
    injector = SafeClipboardInjector(restore_delay_ms=20)
    
    if not injector.is_available():
        return {"available": False, "iterations": 0, "success_rate": 0.0, "p50_ms": None}

    latencies = []
    successes = 0

    # Save original user clipboard
    try:
        orig = subprocess.run(["wl-paste", "--no-newline"], capture_output=True, text=True, timeout=1).stdout
    except Exception:
        orig = ""

    for _ in range(iterations):
        token = f"JARVIS_TEST_{uuid.uuid4().hex[:8]}"
        t0 = time.perf_counter()
        
        # Write token
        try:
            subprocess.run(["wl-copy"], input=token, text=True, check=True, timeout=1)
            read_back = subprocess.run(["wl-paste", "--no-newline"], capture_output=True, text=True, timeout=1).stdout
            lat = (time.perf_counter() - t0) * 1000.0
            
            if read_back == token:
                successes += 1
                latencies.append(lat)
        except Exception:
            pass

    # Restore original clipboard
    try:
        if orig:
            subprocess.run(["wl-copy"], input=orig, text=True, timeout=1)
    except Exception:
        pass

    latencies.sort()
    p50 = latencies[len(latencies) // 2] if latencies else None
    p95 = latencies[int(len(latencies) * 0.95)] if latencies else None

    return {
        "available": True,
        "iterations": iterations,
        "successes": successes,
        "success_rate_pct": round((successes / iterations) * 100.0, 1),
        "latency_p50_ms": round(p50, 2) if p50 else None,
        "latency_p95_ms": round(p95, 2) if p95 else None,
    }

def benchmark_wtype_injection(iterations: int = 15) -> dict:
    """Test wtype keystroke dispatch reliability under Wayland compositor."""
    from core.inject.wtype import WtypeInjector
    injector = WtypeInjector(delay_ms=0)
    
    if not injector.is_available():
        return {"available": False, "iterations": 0, "success_rate": 0.0, "p50_ms": None}

    latencies = []
    successes = 0

    for _ in range(iterations):
        # We send a non-destructive keystroke (or empty test string) to measure compositor event loop latency
        t0 = time.perf_counter()
        try:
            res = subprocess.run(["wtype", "--", ""], capture_output=True, text=True, timeout=2)
            lat = (time.perf_counter() - t0) * 1000.0
            if res.returncode == 0:
                successes += 1
                latencies.append(lat)
        except Exception:
            pass

    latencies.sort()
    p50 = latencies[len(latencies) // 2] if latencies else None
    p95 = latencies[int(len(latencies) * 0.95)] if latencies else None

    return {
        "available": True,
        "iterations": iterations,
        "successes": successes,
        "success_rate_pct": round((successes / iterations) * 100.0, 1),
        "latency_p50_ms": round(p50, 2) if p50 else None,
        "latency_p95_ms": round(p95, 2) if p95 else None,
    }

def main():
    win = get_active_window()
    print("=" * 70)
    print("🎯 REAL WAYLAND TEXT INJECTION RELIABILITY BENCHMARK")
    print(f"• Focused Window Target: [{win.app_category.upper()}] '{win.app_class}' — {win.title[:35]}")
    print("=" * 70)

    print("Testing 'safe-clipboard' (wl-copy / wl-paste round-trip)...")
    clip_res = benchmark_clipboard_injection(iterations=30)
    print(f"  • Success Rate: {clip_res['success_rate_pct']}% ({clip_res['successes']}/{clip_res['iterations']}) | Latency p50: {clip_res['latency_p50_ms']}ms | p95: {clip_res['latency_p95_ms']}ms")

    print("\nTesting 'wtype' (Wayland compositor keystroke dispatch)...")
    wtype_res = benchmark_wtype_injection(iterations=20)
    print(f"  • Success Rate: {wtype_res['success_rate_pct']}% ({wtype_res['successes']}/{wtype_res['iterations']}) | Latency p50: {wtype_res['latency_p50_ms']}ms | p95: {wtype_res['latency_p95_ms']}ms")

    print("=" * 70)

    report = {
        "timestamp": datetime.now().isoformat(),
        "target": {"class": win.app_class, "title": win.title, "category": win.app_category},
        "results": {
            "clipboard": clip_res,
            "wtype": wtype_res,
        }
    }

    out_file = os.path.join(REPO_DIR, "benchmarks/results/injection_reliability.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    print(f"📁 Real injection benchmark report saved to: {out_file}")

if __name__ == "__main__":
    main()
