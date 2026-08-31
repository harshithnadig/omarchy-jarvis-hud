# JARVIS Voice / Omni Jarvis HUD

An offline-first, GPU-accelerated voice dictation keyboard and AI assistant system for Linux/Wayland (Hyprland / Omarchy).

---

## 🎯 Dual-Mode Architecture

JARVIS is built around two architecturally separated modes:

```
+-----------------------------------------------------------------------------------+
|                                  AUDIO CAPTURE                                    |
|                       (Microphone + Silero VAD Endpointing)                       |
+-----------------------------------------+-----------------------------------------+
                                          |
                                          v
+-----------------------------------------------------------------------------------+
|                        LOCAL GPU MULTI-ENGINE SIDE CAR                            |
|             (FastAPI on 127.0.0.1:8765 - CTranslate2 CUDA FP16 / Turbo)           |
+-----------------------------------------+-----------------------------------------+
                                          |
                   +----------------------+----------------------+
                   |                                             |
                   v                                             v
     [MODE A: VOICE KEYBOARD]                      [MODE B: ASSISTANT MODE]
         (Hotkey: Super+Space)                         (Hotkey: Super+J)
                   |                                             |
                   v                                             v
        +--------------------+                        +--------------------+
        |   Context Aware    |                        |   Intent Router    |
        |  Text Polisher &   |                        |  (Fast-Path System |
        |   Backtracking     |                        |  vs Antigravity)   |
        +---------+----------+                        +---------+----------+
                  |                                             |
                  v                                             v
        +--------------------+                        +--------------------+
        |  Direct Wayland    |                        |  Neural Edge-TTS   |
        |   Text Injection   |                        |   Voice Feedback   |
        |  (wtype/wl-copy)   |                        +--------------------+
        +--------------------+
```

### 1. Mode A: Voice Keyboard / Dictation (Primary)
* **Goal:** An ultra-fast, context-aware voice keyboard that types text directly into the active application at the current cursor position (VS Code, terminals, web browsers, chat applications).
* **Pipeline:** Mic Capture → Silero VAD → GPU ASR (`large-v3-turbo`) → Backtracking & Dev Transforms → Context-Aware Text Polish → Direct Wayland Injection (`wtype` / `safe-clipboard`).
* **Isolation:** Zero AI assistant overhead, zero TTS audio, zero cloud calls, zero window focus changes.

### 2. Mode B: JARVIS Assistant (Secondary)
* **Goal:** Dedicated voice AI assistant for desktop system actions and agentic coding.
* **Pipeline:** Voice Query → Fast-Path Local Actions (< 50ms for time/battery/volume/apps) or Antigravity Agent (`agy`) → Audio feedback via Neural Edge-TTS.

---

## 🚀 Unified CLI (`jarvis`)

The `jarvis` CLI provides centralized control over all voice capabilities:

```bash
# Check system status, active engine, and GPU VRAM telemetry
jarvis status

# Run end-to-end hardware & environment diagnostics
jarvis doctor

# Trigger Mode A (Voice Keyboard / Dictation)
jarvis dictate

# Trigger Mode B (Voice AI Assistant)
jarvis assistant

# List available STT engines and their status
jarvis engines

# Switch active STT engine (turbo, large-v3, nemotron)
jarvis engine turbo

# Run scientific STT benchmark suite on GPU
jarvis benchmark run

# Manage background systemd user service
jarvis service [status|start|stop|restart]
```

---

## 📂 Repository Structure & Modules

* **`core/inject/`**: Wayland text injection backends ([`WtypeInjector`](core/inject/wtype.py) for direct typing + [`SafeClipboardInjector`](core/inject/clipboard.py) which preserves previous clipboard history).
* **`core/context/`**: Active window tracking via Hyprland IPC ([`WindowContext`](core/context/active_window.py)), privacy engine ([`PrivacyEngine`](core/context/privacy.py)), and application style profiles ([`StyleProfile`](core/context/profiles.py)).
* **`core/polish/`**: Deterministic text cleanup with backtrack self-correction ([`BacktrackingEngine`](core/polish/backtracking.py)), developer casing transforms ([`DeveloperTransformEngine`](core/polish/developer.py)), and optional local LLM post-processing ([`LocalLLMPolisher`](core/polish/llm.py)).
* **`core/memory/`**: SQLite personal technical dictionary ([`PersonalDictionary`](core/memory/dictionary.py)) and voice snippet expansion ([`SnippetManager`](core/memory/snippets.py)).
* **`core/assistant/`**: Mode B intent routing ([`AssistantRouter`](core/assistant/router.py)), local actions ([`LocalActionExecutor`](core/assistant/actions.py)), and Antigravity agent bridge ([`AntigravityConnector`](core/assistant/antigravity.py)).
* **`core/whisper_engine.py`**: High-performance GPU STT via `faster-whisper` with automatic CUDA dynamic linking and PyAV audio loading.
* **`core/streaming.py`**: Streaming ASR session protocol and chunk-by-chunk partial transcription.
* **`whisrs_sidecar.py`**: Local FastAPI daemon on `127.0.0.1:8765`.
* **`jarvis-dictate`**: Standalone Mode A voice keyboard client.
* **`jarvis-assistant`**: Standalone Mode B assistant client.
* **`config.toml`**: Centralized configuration file (supports user override at `~/.config/jarvis-voice/config.toml`).

---

## 🧪 Testing & Verification

Run the full unit test suite covering all modules:

```bash
pytest -v
```

---

## 📊 Scientific Benchmarking Results (RTX 4060 GPU)

| Engine | Mean WER | Mean CER | Exact Match | Latency p50 | Latency p95 | Mean RTF | VRAM Usage |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **`whisper-large-v3-turbo`** | **26.9%** | **5.9%** | **50.0%** | **576.8 ms** | **787.1 ms** | **0.100x** *(10x real-time)* | **+2,179 MB** |
| **`whisper-large-v3`** | **31.7%** | **6.9%** | **50.0%** | **763.7 ms** | **988.1 ms** | **0.130x** *(7.7x real-time)* | **+3,744 MB** |

See [`docs/MASTER_ROADMAP.md`](docs/MASTER_ROADMAP.md) for detailed architectural specifications.

