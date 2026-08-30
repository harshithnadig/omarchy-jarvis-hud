import os
import time
import json
from datetime import datetime
from typing import List, Dict, Any, Optional

from core.router import EngineRouter
from core.stt_engine import STTError, EngineUnavailableError
from core.polisher import TextPolisher
from core.metrics import compute_wer, compute_cer, compute_summary_stats, normalize_for_eval
from core.gpu_utils import get_gpu_info, VRAMTracker
from benchmarks.dataset import BenchmarkSample

class BenchmarkRunner:
    def __init__(self, router: Optional[EngineRouter] = None):
        self.router = router or EngineRouter()

    def run(
        self,
        samples: List[BenchmarkSample],
        engines: List[str] = ["turbo", "large-v3"],
        apply_polish: bool = True
    ) -> Dict[str, Any]:
        timestamp = datetime.now().isoformat()
        gpu_info = get_gpu_info()

        benchmark_report = {
            "timestamp": timestamp,
            "gpu_hardware": gpu_info,
            "samples_count": len(samples),
            "engines_tested": engines,
            "engine_results": {},
            "detailed_rows": []
        }

        # Benchmark each engine sequentially with VRAM lifecycle management
        for eng_key in engines:
            try:
                eng = self.router.get_engine(eng_key)
            except EngineUnavailableError as e:
                benchmark_report["engine_results"][eng_key] = {
                    "model_name": eng_key,
                    "available": False,
                    "error": str(e),
                    "sample_results": [],
                    "errors": [str(e)]
                }
                continue

            print(f"\n⚡ [Benchmark] Testing Engine '{eng_key}' ({eng.name})...")
            load_time_s = 0.0
            vram_delta_mb = 0.0

            try:
                # Load engine with VRAM tracking
                with VRAMTracker() as vram:
                    t0 = time.perf_counter()
                    eng.load_model()
                    load_time_s = round(time.perf_counter() - t0, 3)
                vram_delta_mb = vram.delta_vram_mb

                eng_stats = {
                    "model_name": eng.name,
                    "load_time_s": load_time_s,
                    "vram_delta_mb": vram_delta_mb,
                    "sample_results": [],
                    "errors": []
                }
                benchmark_report["engine_results"][eng_key] = eng_stats

                # Run inference across all samples
                for sample in samples:
                    if not os.path.exists(sample.audio_path):
                        continue

                    try:
                        res = eng.transcribe_file(sample.audio_path)
                        polished_text = TextPolisher.clean_deterministic(res.text) if apply_polish else res.text

                        wer = None
                        cer = None
                        exact_match = None
                        if sample.reference_text:
                            wer = round(compute_wer(sample.reference_text, polished_text), 4)
                            cer = round(compute_cer(sample.reference_text, polished_text), 4)
                            exact_match = normalize_for_eval(sample.reference_text) == normalize_for_eval(polished_text)

                        sample_res = {
                            "sample_id": sample.id,
                            "raw_text": res.text,
                            "polished_text": polished_text,
                            "latency_ms": res.latency_ms,
                            "rtf": res.rtf,
                            "audio_duration_s": res.audio_duration_s,
                            "wer": wer,
                            "cer": cer,
                            "exact_match": exact_match
                        }
                        eng_stats["sample_results"].append(sample_res)
                        print(f"  • [{sample.id}] {res.latency_ms:6.1f}ms | RTF: {res.rtf:5.3f}x | WER: {wer if wer is not None else 'N/A'}")

                    except Exception as e:
                        err_msg = f"Failed to transcribe {sample.id} on {eng_key}: {e}"
                        eng_stats["errors"].append(err_msg)
                        print(f"  • [{sample.id}] ERROR: {e}")

                # Compute aggregate statistics for this engine
                if eng_stats["sample_results"]:
                    latencies = [s["latency_ms"] for s in eng_stats["sample_results"]]
                    rtfs = [s["rtf"] for s in eng_stats["sample_results"]]
                    wers = [s["wer"] for s in eng_stats["sample_results"] if s["wer"] is not None]
                    cers = [s["cer"] for s in eng_stats["sample_results"] if s["cer"] is not None]
                    exact_matches = [s["exact_match"] for s in eng_stats["sample_results"] if s["exact_match"] is not None]

                    eng_stats["summary"] = {
                        "latency_stats_ms": compute_summary_stats(latencies),
                        "rtf_stats": compute_summary_stats(rtfs),
                        "mean_wer": round(sum(wers) / len(wers), 4) if wers else None,
                        "mean_cer": round(sum(cers) / len(cers), 4) if cers else None,
                        "exact_match_pct": round((sum(exact_matches) / len(exact_matches)) * 100, 2) if exact_matches else None,
                        "total_transcribed": len(eng_stats["sample_results"]),
                        "error_count": len(eng_stats["errors"])
                    }

            finally:
                # Unload engine to free VRAM for subsequent engines
                eng.unload_model()

        return benchmark_report

        return benchmark_report

    @staticmethod
    def format_markdown_table(report: Dict[str, Any]) -> str:
        lines = []
        lines.append("### 📊 STT Multi-Engine Benchmark Results")
        lines.append(f"**GPU Hardware:** {report['gpu_hardware'].get('name', 'N/A')} | **Samples:** {report['samples_count']}")
        lines.append("")
        lines.append("| Engine | Mean WER | Mean CER | Exact Match | Latency p50 (ms) | Latency p95 (ms) | Mean RTF | VRAM Δ |")
        lines.append("| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |")

        for eng_key, stats in report["engine_results"].items():
            if stats.get("available") is False:
                lines.append(f"| `{eng_key}` | *Unavailable* | - | - | - | - | - | - |")
                continue
            summary = stats.get("summary")
            if not summary:
                lines.append(f"| `{eng_key}` | *No Results* | - | - | - | - | - | - |")
                continue

            wer_str = f"{summary['mean_wer'] * 100:.1f}%" if summary["mean_wer"] is not None else "N/A"
            cer_str = f"{summary['mean_cer'] * 100:.1f}%" if summary["mean_cer"] is not None else "N/A"
            match_str = f"{summary['exact_match_pct']:.1f}%" if summary["exact_match_pct"] is not None else "N/A"
            p50_str = f"{summary['latency_stats_ms']['p50']:.1f}"
            p95_str = f"{summary['latency_stats_ms']['p95']:.1f}"
            rtf_str = f"{summary['rtf_stats']['mean']:.3f}x"
            vram_str = f"+{stats.get('vram_delta_mb', 0)}MB"

            lines.append(f"| **`{eng_key}`** | {wer_str} | {cer_str} | {match_str} | {p50_str}ms | {p95_str}ms | {rtf_str} | {vram_str} |")

        return "\n".join(lines)
