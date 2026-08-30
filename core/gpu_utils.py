import subprocess
import shutil
from typing import Dict, Any, Optional

def get_gpu_info() -> Dict[str, Any]:
    """Query NVIDIA GPU metrics via nvidia-smi."""
    if not shutil.which("nvidia-smi"):
        return {
            "available": False,
            "name": "N/A",
            "vram_used_mb": 0.0,
            "vram_total_mb": 0.0,
            "vram_free_mb": 0.0,
            "gpu_util_pct": 0,
            "temp_c": 0
        }

    try:
        cmd = [
            "nvidia-smi",
            "--query-gpu=name,memory.used,memory.total,memory.free,utilization.gpu,temperature.gpu",
            "--format=csv,noheader,nounits"
        ]
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=2)
        if res.returncode == 0 and res.stdout.strip():
            line = res.stdout.strip().split("\n")[0]
            parts = [p.strip() for p in line.split(",")]
            if len(parts) >= 6:
                name = parts[0]
                used = float(parts[1])
                total = float(parts[2])
                free = float(parts[3])
                util = int(parts[4]) if parts[4].isdigit() else 0
                temp = int(parts[5]) if parts[5].isdigit() else 0
                return {
                    "available": True,
                    "name": name,
                    "vram_used_mb": used,
                    "vram_total_mb": total,
                    "vram_free_mb": free,
                    "gpu_util_pct": util,
                    "temp_c": temp
                }
    except Exception:
        pass

    return {
        "available": False,
        "name": "NVIDIA GPU (unresponsive)",
        "vram_used_mb": 0.0,
        "vram_total_mb": 0.0,
        "vram_free_mb": 0.0,
        "gpu_util_pct": 0,
        "temp_c": 0
    }

class VRAMTracker:
    """Context manager to measure VRAM delta during model load or inference."""
    def __init__(self):
        self.initial_vram_mb = 0.0
        self.peak_vram_mb = 0.0
        self.final_vram_mb = 0.0
        self.delta_vram_mb = 0.0

    def __enter__(self):
        info = get_gpu_info()
        self.initial_vram_mb = info.get("vram_used_mb", 0.0)
        self.peak_vram_mb = self.initial_vram_mb
        return self

    def sample_peak(self):
        info = get_gpu_info()
        current = info.get("vram_used_mb", 0.0)
        if current > self.peak_vram_mb:
            self.peak_vram_mb = current

    def __exit__(self, exc_type, exc_val, exc_tb):
        info = get_gpu_info()
        self.final_vram_mb = info.get("vram_used_mb", 0.0)
        if self.final_vram_mb > self.peak_vram_mb:
            self.peak_vram_mb = self.final_vram_mb
        self.delta_vram_mb = round(self.final_vram_mb - self.initial_vram_mb, 2)
