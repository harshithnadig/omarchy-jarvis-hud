#!/usr/bin/env python3
"""
JARVIS Cache-Aware Streaming Latency & State Verification Benchmark.
Streams audio in 160ms chunks through CacheAwareStreamingSession,
measuring time-to-first-partial, per-step encoder latency, and emitted partial progressions.
"""
import os
import sys
import time
import json
import wave
from datetime import datetime

REPO_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO_DIR not in sys.path:
    sys.path.insert(0, REPO_DIR)

from core.router import EngineRouter
from core.streaming import CacheAwareStreamingSession

def run_streaming_benchmark(audio_path: str, engine_key: str = "turbo", chunk_duration_s: float = 0.16) -> dict:
    router = EngineRouter(default_engine=engine_key)
    engine = router.get_engine(engine_key)

    if not os.path.exists(audio_path):
        print(f"❌ Audio file not found: {audio_path}")
        sys.exit(1)

    with wave.open(audio_path, "rb") as wf:
        n_channels = wf.getnchannels()
        sampwidth = wf.getsampwidth()
        framerate = wf.getframerate()
        n_frames = wf.getnframes()
        pcm_raw = wf.readframes(n_frames)

    total_duration_s = n_frames / float(framerate)
    bytes_per_chunk = int(chunk_duration_s * framerate * sampwidth)
    total_chunks = (len(pcm_raw) + bytes_per_chunk - 1) // bytes_per_chunk

    print("=" * 70)
    print(f"⚡ STREAMING BENCHMARK: Engine '{engine.name}'")
    print(f"• Audio: {os.path.basename(audio_path)} ({total_duration_s:.2f}s, {total_chunks} chunks @ {chunk_duration_s*1000:.0f}ms)")
    print("=" * 70)

    session = CacheAwareStreamingSession(
        engine=engine,
        sample_rate=framerate,
        chunk_duration_s=chunk_duration_s,
        agreement_threshold=2
    )

    partials_emitted = []
    chunk_latencies_ms = []
    first_partial_time_ms = None
    start_time = time.perf_counter()

    for idx in range(total_chunks):
        chunk = pcm_raw[idx * bytes_per_chunk : (idx + 1) * bytes_per_chunk]
        t0 = time.perf_counter()
        partial = session.push_chunk(chunk)
        step_lat = (time.perf_counter() - t0) * 1000.0
        chunk_latencies_ms.append(step_lat)

        if partial and partial.strip():
            if first_partial_time_ms is None:
                first_partial_time_ms = (time.perf_counter() - start_time) * 1000.0
            partials_emitted.append({
                "chunk_idx": idx + 1,
                "elapsed_ms": round((time.perf_counter() - start_time) * 1000.0, 1),
                "partial_text": partial
            })
            print(f"  • Chunk {idx+1:02d}/{total_chunks:02d} ({step_lat:4.1f}ms): \"{partial}\"")

    t_finalize_0 = time.perf_counter()
    result = session.finalize()
    finalize_lat_ms = (time.perf_counter() - t_finalize_0) * 1000.0
    total_elapsed_s = time.perf_counter() - start_time

    chunk_latencies_ms.sort()
    p50_step = chunk_latencies_ms[len(chunk_latencies_ms) // 2] if chunk_latencies_ms else 0.0
    p95_step = chunk_latencies_ms[int(len(chunk_latencies_ms) * 0.95)] if chunk_latencies_ms else 0.0

    print("=" * 70)
    print(f"🎯 FINAL TEXT: \"{result.text}\"")
    print(f"• Total Duration: {total_duration_s:.2f}s | Elapsed: {total_elapsed_s:.2f}s | RTF: {total_elapsed_s/total_duration_s:.2f}x")
    print(f"• Time-to-First-Partial: {first_partial_time_ms:.1f}ms" if first_partial_time_ms else "• No partials emitted during stream")
    print(f"• Per-Chunk Latency p50: {p50_step:.2f}ms | p95: {p95_step:.2f}ms")
    print(f"• Finalize Latency: {finalize_lat_ms:.2f}ms")
    print("=" * 70)

    report = {
        "timestamp": datetime.now().isoformat(),
        "engine": engine.name,
        "audio_file": os.path.basename(audio_path),
        "total_duration_s": round(total_duration_s, 2),
        "total_chunks": total_chunks,
        "first_partial_time_ms": round(first_partial_time_ms, 2) if first_partial_time_ms else None,
        "per_chunk_p50_ms": round(p50_step, 2),
        "per_chunk_p95_ms": round(p95_step, 2),
        "finalize_latency_ms": round(finalize_lat_ms, 2),
        "rtf": round(total_elapsed_s / total_duration_s, 3),
        "partials": partials_emitted,
        "final_text": result.text
    }

    out_file = os.path.join(REPO_DIR, "benchmarks/results/streaming_benchmark.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    print(f"📁 Streaming benchmark results saved to: {out_file}")
    return report

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--audio", default="benchmarks/corpus/clean_01_greeting.wav", help="Audio file to stream")
    parser.add_argument("--engine", default="turbo", help="Engine key (turbo, large-v3, nemotron)")
    args = parser.parse_args()

    # Convert input audio to 16kHz mono WAV if not already WAV
    audio_target = args.audio
    if not audio_target.endswith(".wav"):
        import subprocess
        tmp_wav = "/tmp/stream_bench_target.wav"
        subprocess.run(["ffmpeg", "-y", "-i", audio_target, "-ar", "16000", "-ac", "1", tmp_wav], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        audio_target = tmp_wav

    run_streaming_benchmark(audio_target, engine_key=args.engine)
