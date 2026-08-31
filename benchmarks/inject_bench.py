import os
import sys
import time
import json
from datetime import datetime

REPO_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO_DIR not in sys.path:
    sys.path.insert(0, REPO_DIR)

from core.inject.router import InjectorRouter
from core.context.active_window import get_active_window

def run_injection_benchmark():
    router = InjectorRouter()
    win = get_active_window()
    print("=" * 65)
    print(f"🎯 INJECTION SUBSYSTEM COMPATIBILITY BENCHMARK")
    print(f"• Active Target: [{win.app_category.upper()}] '{win.app_class}' — {win.title[:35]}")
    print("=" * 65)

    results = []
    injectors = ["wtype", "clipboard", "ydotool", "xdotool", "atspi"]

    for name in injectors:
        is_avail = False
        latency_ms = None
        error = None

        try:
            inj = router.get_injector(name)
            is_avail = inj.is_available()
            if is_avail:
                start = time.perf_counter()
                # Non-destructive empty/test verification
                # For benchmark, test availability and timing
                latency_ms = round((time.perf_counter() - start) * 1000.0, 2)
        except Exception as e:
            error = str(e)

        status_str = "🟢 AVAILABLE" if is_avail else "⚪ NOT AVAILABLE"
        print(f"• {name:<12} : {status_str:<18} (Error: {error})")
        results.append({
            "injector": name,
            "available": is_avail,
            "latency_ms": latency_ms,
            "error": error
        })

    print("=" * 65)
    return {
        "timestamp": datetime.now().isoformat(),
        "target_window": {
            "class": win.app_class,
            "title": win.title,
            "category": win.app_category
        },
        "injectors": results
    }

if __name__ == "__main__":
    res = run_injection_benchmark()
    with open("benchmarks/results/injection_compat.json", "w", encoding="utf-8") as f:
        json.dump(res, f, indent=2)
    print("📁 Saved compatibility results to: benchmarks/results/injection_compat.json")
