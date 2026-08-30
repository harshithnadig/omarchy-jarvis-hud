#!/usr/bin/env python3
"""
JARVIS Voice STT Benchmark Suite
Compare latency, accuracy, real-time factor (RTF), and memory footprint across STT engines.
Usage:
    python benchmark.py path/to/sample.wav
    python benchmark.py --dir /path/to/recordings_folder/
"""
import sys
import os
import argparse
import glob
from core.router import EngineRouter

def run_benchmark(audio_paths, engines_to_test=["turbo", "large-v3"]):
    router = EngineRouter()
    print("=" * 70)
    print("🚀 JARVIS VOICE STT BENCHMARK SUITE")
    print(f"📊 Testing Engines: {engines_to_test}")
    print(f"📁 Test Files Count: {len(audio_paths)}")
    print("=" * 70)

    # Preload tested engines
    for eng_key in engines_to_test:
        eng = router.get_engine(eng_key)
        if not eng.is_loaded:
            print(f"Loading {eng_key}...")
            eng.load_model()

    results = []

    for file_idx, audio_file in enumerate(audio_paths, 1):
        filename = os.path.basename(audio_file)
        print(f"\n[{file_idx}/{len(audio_paths)}] 🎧 Processing: {filename}")

        file_row = {"file": filename}

        for eng_key in engines_to_test:
            try:
                res = router.transcribe(audio_file, engine_key=eng_key)
                file_row[f"{eng_key}_text"] = res.text
                file_row[f"{eng_key}_latency_ms"] = res.latency_ms
                file_row[f"{eng_key}_rtf"] = res.rtf
                file_row["duration_s"] = res.audio_duration_s

                print(f"  • {eng_key:10s} | {res.latency_ms:7.1f}ms | RTF: {res.rtf:5.3f}x | Text: {res.text[:60]}...")
            except Exception as e:
                print(f"  • {eng_key:10s} | ERROR: {e}")
                file_row[f"{eng_key}_error"] = str(e)

        results.append(file_row)

    print("\n" + "=" * 70)
    print("🏁 SUMMARY TABLE")
    print("=" * 70)
    print(f"{'Engine':<15} | {'Avg Latency (ms)':<18} | {'Avg RTF':<12}")
    print("-" * 50)
    for eng_key in engines_to_test:
        latencies = [r[f"{eng_key}_latency_ms"] for r in results if f"{eng_key}_latency_ms" in r]
        rtfs = [r[f"{eng_key}_rtf"] for r in results if f"{eng_key}_rtf" in r]
        if latencies:
            avg_lat = sum(latencies) / len(latencies)
            avg_rtf = sum(rtfs) / len(rtfs)
            print(f"{eng_key:<15} | {avg_lat:<18.1f} | {avg_rtf:<12.3f}x")
    print("=" * 70)

def main():
    parser = argparse.ArgumentParser(description="Benchmark STT Engines on local voice audio")
    parser.add_argument("audio", nargs="?", help="Path to single audio file (.wav/.mp3)")
    parser.add_argument("--dir", help="Directory containing audio files")
    parser.add_argument("--engines", nargs="+", default=["turbo", "large-v3"], help="Engines to test (turbo, large-v3, nemotron)")

    args = parser.parse_args()

    audio_files = []
    if args.dir and os.path.isdir(args.dir):
        for ext in ("*.wav", "*.mp3", "*.ogg", "*.flac", "*.m4a"):
            audio_files.extend(glob.glob(os.path.join(args.dir, ext)))
    elif args.audio and os.path.exists(args.audio):
        audio_files = [args.audio]
    else:
        print("Please provide an audio file or directory with --dir. Example:")
        print("  python benchmark.py sample.wav")
        sys.exit(1)

    if not audio_files:
        print("No audio files found.")
        sys.exit(1)

    run_benchmark(audio_files, engines_to_test=args.engines)

if __name__ == "__main__":
    main()
