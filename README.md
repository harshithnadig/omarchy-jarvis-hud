# JARVIS Voice / Omni Jarvis HUD

An offline-first, GPU-accelerated voice dictation and assistant system for Linux/Wayland (Hyprland / Omarchy).

---

## 🎯 Dual-Mode Architecture

JARVIS is built around two architecturally separated modes:

### 1. Mode A: Voice Keyboard / Dictation (Primary)
* **Goal:** A low-latency, privacy-preserving voice keyboard that lets you speak naturally and have polished text inserted directly at your active cursor across Linux applications (VS Code, Chrome, terminals, chat apps).
* **Behavior:** Local capture → Silero VAD → GPU ASR (`whisper-large-v3-turbo` / `whisper-large-v3`) → Safe deterministic polish → Direct text injection.
* **Boundary:** Does not call AI assistants, does not speak via TTS, and does not execute OS commands.

### 2. Mode B: JARVIS Assistant (Secondary)
* **Goal:** Interactive desktop AI assistant for executing tasks and voice queries.
* **Behavior:** Voice query → STT → Intent routing → Local fast-path or Antigravity AI Agent (`agy`) → Concise voice response via Neural Edge-TTS.

---

## 📂 Repository Structure & Components

* **`core/stt_engine.py`**: Abstract base `STTEngine` contract with explicit exception hierarchy (`EngineUnavailableError`, `ModelLoadError`, `InferenceError`) and genuine metric dataclass (`TranscriptionResult`).
* **`core/whisper_engine.py`**: Local GPU/CPU transcription via `faster-whisper` (CTranslate2 FP16/INT8).
* **`core/nemotron_engine.py`**: NVIDIA NeMo ASR engine integration (cache-aware streaming targeted for Phase 4).
* **`core/router.py`**: Multi-engine router supporting dynamic engine switching.
* **`core/polisher.py`**: Safe, non-destructive deterministic text polisher (stutter deduplication with intentional repetition preservation, punctuation spacing, dev operators).
* **`whisrs_sidecar.py`**: High-performance local FastAPI service on port `8765`.
* **`jarvis-ptt`**: Push-to-talk voice client with Silero VAD.
* **`jarvis_daemon.py`**: Continuous listening assistant daemon (experimental).
* **`benchmark.py`**: Reproducible benchmarking suite measuring latency and Real-Time Factor (RTF).
* **`docs/MASTER_ROADMAP.md`**: Master product specification and 12-phase development roadmap.

---

## 🚀 Status & Roadmap

| Feature | Status | Notes |
| :--- | :---: | :--- |
| **Whisper Large-v3-Turbo** | ✅ Available | Default fast multilingual offline engine |
| **Whisper Large-v3** | ✅ Available | Maximum accuracy multilingual offline engine |
| **Deterministic Text Polish** | ✅ Available | Filler cleaning, stutter deduplication, dev operators |
| **Multi-Engine Sidecar** | ✅ Available | Local FastAPI daemon on `127.0.0.1:8765` |
| **Unit Test Suite** | ✅ Available | `pytest` test suite covering core engine & router contracts |
| **Direct Wayland Text Injection** | 📋 Planned (Phase 3) | AT-SPI, wtype, ydotool adapter hierarchy |
| **True Cache-Aware Streaming** | 📋 Planned (Phase 4) | Streaming session API and NeMo cache streaming |
| **Context & Privacy Engine** | 📋 Planned (Phase 6) | Active window metadata, sensitive field masking |

See [`docs/MASTER_ROADMAP.md`](docs/MASTER_ROADMAP.md) for full phase-by-phase milestones.

---

## 🧪 Testing

Run the local unit test suite:

```bash
pytest -v
```

