import os
import shutil
import urllib.request
import json
import sounddevice as sd
from typing import Dict, List, Tuple

from core.gpu_utils import get_gpu_info
from core.context.active_window import get_active_window
from core.whisper_engine import ensure_cuda_libraries

def run_diagnostics() -> Dict[str, Any]:
    """Execute end-to-end system and environment health checks."""
    results = {
        "status": "PASS",
        "checks": []
    }

    def add_check(category: str, item: str, passed: bool, details: str = ""):
        results["checks"].append({
            "category": category,
            "item": item,
            "passed": passed,
            "details": details
        })
        if not passed:
            results["status"] = "FAIL"

    # 1. GPU & CUDA
    gpu = get_gpu_info()
    if gpu.get("available"):
        add_check("GPU", "NVIDIA GPU Hardware", True, f"{gpu['name']} ({gpu['vram_free_mb']}MB free / {gpu['vram_total_mb']}MB total)")
    else:
        add_check("GPU", "NVIDIA GPU Hardware", False, "nvidia-smi not detected or GPU offline")

    try:
        ensure_cuda_libraries()
        import ctranslate2
        cuda_types = ctranslate2.get_supported_compute_types("cuda")
        add_check("CUDA", "CTranslate2 CUDA Compute Types", True, f"Supported: {cuda_types}")
    except Exception as e:
        add_check("CUDA", "CTranslate2 CUDA Compute Types", False, str(e))

    # 2. Audio Capture
    try:
        devices = sd.query_devices()
        default_in = sd.query_devices(kind='input')
        add_check("Audio", "Microphone Input Device", True, f"{default_in['name']} (Sample Rate: {default_in['default_samplerate']}Hz)")
    except Exception as e:
        add_check("Audio", "Microphone Input Device", False, str(e))

    # 3. Wayland & Compositor
    is_hypr = shutil.which("hyprctl") is not None
    add_check("Wayland", "Hyprland IPC", is_hypr, "hyprctl found" if is_hypr else "hyprctl not found (using standard Wayland fallback)")

    win = get_active_window()
    add_check("Wayland", "Active Window Tracking", True, f"Class: '{win.app_class}', Title: '{win.title}' (Category: {win.app_category})")

    # 4. Text Injectors
    has_wtype = shutil.which("wtype") is not None
    add_check("Injection", "wtype (Direct Keystroke Typing)", has_wtype, "/usr/bin/wtype" if has_wtype else "Missing wtype package")

    has_wl_copy = shutil.which("wl-copy") is not None
    has_wl_paste = shutil.which("wl-paste") is not None
    add_check("Injection", "wl-clipboard (Safe Paste)", (has_wl_copy and has_wl_paste), "wl-copy & wl-paste available" if (has_wl_copy and has_wl_paste) else "Missing wl-clipboard")

    # 5. Assistant & Antigravity
    has_agy = shutil.which("agy") is not None
    add_check("Assistant", "Antigravity CLI (agy)", has_agy, "agy CLI available" if has_agy else "agy not in PATH")

    # 6. Sidecar Service
    sidecar_online = False
    sidecar_details = "Not responding on 127.0.0.1:8765"
    try:
        with urllib.request.urlopen("http://127.0.0.1:8765/health", timeout=1.5) as resp:
            data = json.loads(resp.read().decode())
            sidecar_online = True
            sidecar_details = f"ONLINE (Active Engine: {data.get('active_engine')})"
    except Exception as e:
        sidecar_details = f"Offline ({e})"

    add_check("Service", "JARVIS GPU Sidecar Server", sidecar_online, sidecar_details)

    return results

def print_doctor_report():
    report = run_diagnostics()
    print("=" * 70)
    print(f"🩺 JARVIS SYSTEM & HEALTH DIAGNOSTICS: [{report['status']}]")
    print("=" * 70)

    current_cat = ""
    for c in report["checks"]:
        if c["category"] != current_cat:
            current_cat = c["category"]
            print(f"\n[{current_cat}]")

        icon = "✅" if c["passed"] else "❌"
        print(f"  {icon} {c['item']:<35} : {c['details']}")

    print("\n" + "=" * 70)
