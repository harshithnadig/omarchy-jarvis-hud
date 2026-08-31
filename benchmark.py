#!/usr/bin/env python3
"""
JARVIS Voice STT Scientific Benchmark Suite
Measures Word Error Rate (WER), Character Error Rate (CER), Latency Distributions (p50, p95),
Real-Time Factor (RTF), and VRAM across STT engines.

Usage:
    # 1. Run benchmark against a manifest file:
    python benchmark.py run --manifest benchmarks/corpus/manifest.json

    # 2. Run benchmark on single audio file:
    python benchmark.py file sample.wav --ref "Expected spoken text"

    # 3. Record a local voice benchmark sample from microphone:
    python benchmark.py record --id dev_sample_01 --cat developer_terms --ref "const response = await fetch(url)"

    # 4. Generate synthetic test dataset for automated verification:
    python benchmark.py generate-synthetic --outdir benchmarks/corpus
"""
import os
import sys
import glob
import json
import argparse
import asyncio
import sounddevice as sd
import numpy as np
import wave
from datetime import datetime

from core.router import EngineRouter
from benchmarks.dataset import BenchmarkSample, load_manifest, save_manifest
from benchmarks.runner import BenchmarkRunner

def cmd_run(args):
    samples = []
    if args.manifest:
        samples = load_manifest(args.manifest)
    elif args.dir:
        for ext in ("*.wav", "*.mp3", "*.flac", "*.ogg"):
            for p in glob.glob(os.path.join(args.dir, ext)):
                samples.append(BenchmarkSample(id=os.path.splitext(os.path.basename(p))[0], audio_path=p))
    elif args.file:
        samples = [BenchmarkSample(id="single_sample", audio_path=args.file, reference_text=args.ref or "")]
    else:
        # Default fallback to checking benchmarks/corpus/manifest.json
        default_manifest = "benchmarks/corpus/manifest.json"
        if os.path.exists(default_manifest):
            samples = load_manifest(default_manifest)
        else:
            print("❌ No input provided. Specify --manifest <path>, --dir <path>, or a file path.")
            sys.exit(1)

    if not samples:
        print("❌ No valid audio samples found to benchmark.")
        sys.exit(1)

    print(f"🚀 Starting Benchmark: {len(samples)} samples on engines {args.engines}")
    runner = BenchmarkRunner()
    report = runner.run(samples=samples, engines=args.engines, apply_polish=not args.raw)

    # Print Markdown Summary Table
    print("\n" + "=" * 70)
    print(runner.format_markdown_table(report))
    print("=" * 70 + "\n")

    # Save JSON report
    out_dir = args.output or "benchmarks/results"
    os.makedirs(out_dir, exist_ok=True)
    report_file = os.path.join(out_dir, f"benchmark_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    print(f"📁 Detailed results saved to: {report_file}")


def cmd_record(args):
    """Record a voice sample from microphone and add to manifest."""
    os.makedirs(args.outdir, exist_ok=True)
    audio_path = os.path.join(args.outdir, f"{args.id}.wav")

    print("=" * 60)
    print(f"🎙️ Recording sample '{args.id}' (Category: {args.cat})")
    print(f"📖 Reference Text: \"{args.ref}\"")
    print("👉 Press ENTER to start recording (3 seconds countdown)...")
    input()

    sample_rate = 16000
    duration = args.duration
    print(f"🔴 RECORDING for {duration} seconds... Speak now!")
    audio_data = sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=1, dtype='int16')
    sd.wait()
    print("⏹️ Recording finished!")

    with wave.open(audio_path, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(audio_data.tobytes())

    print(f"💾 Audio saved: {audio_path}")

    # Update manifest
    manifest_path = os.path.join(args.outdir, "manifest.json")
    existing_samples = []
    if os.path.exists(manifest_path):
        try:
            existing_samples = load_manifest(manifest_path)
        except Exception:
            pass

    # Filter out existing with same ID if updating
    existing_samples = [s for s in existing_samples if s.id != args.id]
    existing_samples.append(BenchmarkSample(
        id=args.id,
        audio_path=f"{args.id}.wav",
        reference_text=args.ref,
        category=args.cat,
        duration_s=duration
    ))

    save_manifest(existing_samples, manifest_path)
    print(f"✅ Manifest updated: {manifest_path} ({len(existing_samples)} total samples)")


def cmd_generate_synthetic(args):
    """Generate synthetic reference samples using Edge-TTS for all items in manifest.json."""
    import edge_tts
    out_dir = args.outdir
    os.makedirs(out_dir, exist_ok=True)
    manifest_path = os.path.join(out_dir, "manifest.json")

    if not os.path.exists(manifest_path):
        print(f"❌ Manifest not found at '{manifest_path}'")
        sys.exit(1)

    with open(manifest_path, "r", encoding="utf-8") as f:
        raw_items = json.load(f)

    samples = []
    print(f"🔨 Generating {len(raw_items)} synthetic benchmark samples in '{out_dir}'...")

    async def generate_all():
        for item in raw_items:
            audio_filename = item["audio_path"]
            if not audio_filename.endswith((".mp3", ".wav")):
                audio_filename += ".mp3"
            wav_path = os.path.join(out_dir, os.path.basename(audio_filename))

            # Select voice accent
            voice = "en-IN-PrabhatNeural" if item.get("category") == "indian_english" else "en-US-ChristopherNeural"
            
            communicate = edge_tts.Communicate(item["reference_text"], voice)
            await communicate.save(wav_path)

            samples.append(BenchmarkSample(
                id=item["id"],
                audio_path=os.path.basename(wav_path),
                reference_text=item["reference_text"],
                category=item.get("category", "general"),
                language=item.get("language", "en"),
                tags=item.get("tags", [])
            ))
            print(f"  • Generated [{item.get('category')}]: {item['id']}")

    asyncio.run(generate_all())
    save_manifest(samples, manifest_path)
    print(f"✅ Synthetic corpus created at '{manifest_path}' with {len(samples)} samples.")


def main():
    parser = argparse.ArgumentParser(description="JARVIS Scientific Voice Benchmark Suite")
    subparsers = parser.add_subparsers(dest="subcommand", help="Subcommands")

    # Run subcommand
    parser_run = subparsers.add_parser("run", help="Run STT benchmark suite")
    parser_run.add_argument("--manifest", help="Path to manifest.json")
    parser_run.add_argument("--dir", help="Directory of audio files")
    parser_run.add_argument("--file", help="Single audio file")
    parser_run.add_argument("--ref", help="Reference text for single audio file")
    parser_run.add_argument("--engines", nargs="+", default=["turbo", "large-v3"], help="Engines to benchmark")
    parser_run.add_argument("--raw", action="store_true", help="Bypass text polishing")
    parser_run.add_argument("--output", help="Output directory for benchmark results")

    # Record subcommand
    parser_rec = subparsers.add_parser("record", help="Record audio sample from mic for benchmark corpus")
    parser_rec.add_argument("--id", required=True, help="Unique sample identifier (e.g. dev_01)")
    parser_rec.add_argument("--cat", default="general", help="Category: clean_english, dev_terms, indian_english, etc.")
    parser_rec.add_argument("--ref", required=True, help="Ground truth reference transcript")
    parser_rec.add_argument("--duration", type=float, default=6.0, help="Recording duration in seconds")
    parser_rec.add_argument("--outdir", default="benchmarks/corpus", help="Directory to save recording & manifest")

    # Generate Synthetic subcommand
    parser_synth = subparsers.add_parser("generate-synthetic", help="Generate synthetic test audio samples")
    parser_synth.add_argument("--outdir", default="benchmarks/corpus", help="Output directory for synthetic corpus")

    args, unknown = parser.parse_known_args()

    # Legacy CLI compatibility: python benchmark.py sample.wav
    if not args.subcommand and len(sys.argv) > 1 and not sys.argv[1].startswith("-"):
        args.subcommand = "run"
        args.file = sys.argv[1]
        args.ref = None
        args.manifest = None
        args.dir = None
        args.engines = ["turbo", "large-v3"]
        args.raw = False
        args.output = None
        cmd_run(args)
        return

    if args.subcommand == "run":
        cmd_run(args)
    elif args.subcommand == "record":
        cmd_record(args)
    elif args.subcommand == "generate-synthetic":
        cmd_generate_synthetic(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
