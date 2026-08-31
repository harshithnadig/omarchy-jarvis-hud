#!/usr/bin/env python3
"""
JARVIS End-to-End Real Application Textbox Injection Benchmark.
Spawns a real Wayland application window (Foot terminal / text entry),
injects randomized unique tokens via wtype and clipboard,
reads back the received text from the application,
and computes exact byte-for-byte insertion reliability and round-trip latency.
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

def run_e2e_wtype_benchmark(iterations: int = 10) -> dict:
    """Run real E2E textbox insertion benchmark via wtype."""
    successes = 0
    latencies = []
    out_file = "/tmp/jarvis_e2e_wtype.txt"

    print(f"🚀 Running {iterations} E2E real-window insertion tests via 'wtype'...")

    for i in range(iterations):
        if os.path.exists(out_file):
            os.remove(out_file)

        token = f"JARVIS_E2E_WTYPE_{uuid.uuid4().hex[:6]}"
        t0 = time.perf_counter()

        # Spawn temporary Wayland text receiver window
        proc = subprocess.Popen(
            ["foot", "--title", "JARVIS_BENCH_WTYPE", "sh", "-c", f'read -r line; echo "$line" > {out_file}'],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        time.sleep(0.35)  # Wait for Wayland surface map & Hyprland focus

        try:
            # Inject token via wtype + Return
            subprocess.run(["wtype", "--", token], check=True, timeout=2)
            subprocess.run(["wtype", "-k", "Return"], check=True, timeout=2)
            proc.wait(timeout=2.5)

            lat = (time.perf_counter() - t0) * 1000.0

            if os.path.exists(out_file):
                with open(out_file, "r") as f:
                    received = f.read().strip()
                if received == token:
                    successes += 1
                    latencies.append(lat)
                    print(f"  • Iteration {i+1:02d}: ✅ EXACT MATCH ({lat:.1f}ms)")
                else:
                    print(f"  • Iteration {i+1:02d}: ❌ MISMATCH ('{received}' != '{token}')")
            else:
                print(f"  • Iteration {i+1:02d}: ❌ NO OUTPUT FILE")
        except Exception as e:
            print(f"  • Iteration {i+1:02d}: ❌ EXCEPTION ({e})")
            if proc.poll() is None:
                proc.kill()

    latencies.sort()
    p50 = latencies[len(latencies) // 2] if latencies else None
    p95 = latencies[int(len(latencies) * 0.95)] if latencies else None

    return {
        "iterations": iterations,
        "successes": successes,
        "success_rate_pct": round((successes / iterations) * 100.0, 1),
        "latency_p50_ms": round(p50, 2) if p50 else None,
        "latency_p95_ms": round(p95, 2) if p95 else None,
    }

def main():
    print("=" * 70)
    print("🎯 REAL END-TO-END APPLICATION TEXTBOX INJECTION BENCHMARK")
    print("• Target: Wayland / Hyprland Real Native Application Window")
    print("=" * 70)

    results = run_e2e_wtype_benchmark(iterations=10)

    print("\n" + "=" * 70)
    print(f"📊 SUMMARY: {results['success_rate_pct']}% Insertion Reliability ({results['successes']}/{results['iterations']})")
    print(f"• Latency p50: {results['latency_p50_ms']} ms | p95: {results['latency_p95_ms']} ms")
    print("=" * 70)

    out_file = os.path.join(REPO_DIR, "benchmarks/results/e2e_injection_results.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "target": "Foot / Wayland Native Window",
            "benchmark": results
        }, f, indent=2)
    print(f"📁 Detailed report saved to: {out_file}")

if __name__ == "__main__":
    main()
