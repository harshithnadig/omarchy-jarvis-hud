# JARVIS Voice: Master Product Specification & Architectural Roadmap

**Repository:** `harshithnadig/omarchy-jarvis-hud`  
**Mission:** The best local-first, offline voice dictation system & voice keyboard for Linux/Wayland, with a secondary, architecturally isolated JARVIS Assistant Mode.

---

## 1. Product Definition & Modes

The product provides two explicitly separate user experiences:

### Mode A: JARVIS Dictation (Voice Keyboard) — PRIMARY
* **Hotkey:** e.g., `Super + Space` (press/hold or toggle)
* **Pipeline:**
  ```text
  Press / Hold Hotkey
  → Microphone captures audio immediately
  → Silero VAD detects speech
  → Partial transcription streams (if supported)
  → Speech ends / Key released
  → Final ASR result
  → Safe deterministic cleanup & context correction
  → Text inserted directly at active cursor
  ```
* **Strict Boundary:** Must **NOT** invoke Antigravity, answer the user, speak via TTS, or perform OS actions.
* **Target Applications:** Chrome/Chromium, Firefox, VS Code, Cursor/Electron apps, Foot/Kitty/Alacritty terminals, Discord, Slack, GTK & Qt apps, native Wayland & XWayland apps.
* **Experience:** Invisible, ultra-low latency voice keyboard: *Speak → text appears*.

### Mode B: JARVIS Assistant — SECONDARY
* **Hotkey:** e.g., `Super + J`
* **Pipeline:**
  ```text
  Speech
  → STT
  → Intent Routing (Local Fast-Path vs Antigravity Agent)
  → Execute Action (with safety permission classes)
  → Concise Spoken Response (Neural Edge-TTS)
  ```
* **Strict Boundary:** Assistant Mode must **NOT** contaminate the low-latency Dictation Mode pipeline.

---

## 2. Architectural Direction

```text
                           JARVIS VOICE CORE

                                MIC
                                 │
                           Audio Capture
                                 │
                    Noise suppression / AGC
                                 │
                            Silero VAD
                                 │
                         Endpoint Detector
                                 │
                         Streaming ASR API
                                 │
                ┌────────────────┼────────────────┐
                │                │                │
         Whisper Turbo      Whisper Large-v3   Nemotron
                │                │                │
                └────────────────┼────────────────┘
                                 │
                          Raw Transcript
                                 │
                    Safe deterministic cleanup
                                 │
                           Context Engine
                                 │
                   Personal dictionary/memory
                                 │
                       Optional local LLM
                                 │
                           Final Transcript
                                 │
                   ┌─────────────┴─────────────┐
                   │                           │
              DICTATION                    ASSISTANT
                   │                           │
           Text Injection               Intent Router
                   │                           │
              Focused App             Antigravity/tools
```

---

## 3. Target Repository Structure

```text
omarchy-jarvis-hud/
├── core/
│   ├── stt/
│   │   ├── base.py
│   │   ├── router.py
│   │   ├── whisper.py
│   │   └── nemotron.py
│   ├── audio/
│   │   ├── capture.py
│   │   ├── vad.py
│   │   └── endpoint.py
│   ├── context/
│   │   ├── active_window.py
│   │   ├── accessibility.py
│   │   └── privacy.py
│   ├── polish/
│   │   ├── deterministic.py
│   │   ├── correction.py
│   │   └── llm.py
│   ├── inject/
│   │   ├── base.py
│   │   ├── atspi.py
│   │   ├── wtype.py
│   │   ├── ydotool.py
│   │   ├── xdotool.py
│   │   └── clipboard.py
│   ├── memory/
│   │   ├── dictionary.py
│   │   ├── corrections.py
│   │   └── snippets.py
│   └── assistant/
│       ├── router.py
│       ├── actions.py
│       └── antigravity.py
├── ui/
├── benchmarks/
├── tests/
├── scripts/
└── docs/
```

---

## 4. Development Phases

### Phase 0: Repository Truth & Cleanup
* Complete codebase audit.
* Eliminate fake placeholders and hardcoded confidence values.
* Correct misleading marketing claims in README and comments.
* Establish standard exception hierarchy (`EngineUnavailableError`, `ModelLoadError`, `InferenceError`).
* Make paths portable and remove user-specific hardcoded paths.
* Establish unit and integration test suite (`pytest`).

### Phase 1: Scientific STT Foundation
* Finalize `STTEngine` interfaces.
* Support Whisper Large-v3 and Whisper Large-v3-Turbo via `faster-whisper` (CTranslate2).
* Functional Nemotron batch baseline (raising explicit errors if dependencies or models are missing).
* Build reproducible local benchmark corpus (WER, CER, RTF, Latency p50/p95, VRAM).

### Phase 2: Perfect Push-to-Talk Dictation Loop
* Robust audio capture with Silero VAD.
* End-to-end hotkey → capture → STT → safe deterministic polish → direct text injection under Hyprland.
* Isolate from assistant and TTS logic.

### Phase 3: Wayland Injection Reliability
* Dedicated `TextInjector` subsystem with fallback priority (AT-SPI, wtype, ydotool, xdotool, safe clipboard fallback).
* Focus preservation (non-stealing overlay/HUD).
* Application compatibility matrix across browsers, IDEs, terminals, Electron, GTK, Qt.

### Phase 4: True Streaming ASR
* Streaming STT session API (`start_session`, `push_audio`, `get_partial`, `finalize`).
* Real cache-aware streaming for Nemotron.
* Non-focus-stealing live dictation overlay widget with partial transcription.

### Phase 5: Smart Text Polishing Engine
* Safe deterministic cleanup without destructive deletions.
* Intentional repetition preservation.
* Backtracking / self-correction engine ("X... actually Y").
* Developer shorthand mode (`=>`, `===`, `&&`, `?.`, casing transformations).

### Phase 6: Context Awareness
* Active window metadata & application profiles (Code, Chat, Terminal, Email).
* Focused field inspection (AT-SPI accessibility where permitted).
* Privacy boundaries (automatic shutoff for password/secret fields, Private Mode).

### Phase 7: Personalization & Memory
* SQLite personal dictionary (spoken form → canonical form, aliases, technical terms).
* Correction learning with user confirmation.
* Voice snippets.

### Phase 8: Local LLM Polisher (Optional)
* Constrained local LLM rewriting (small 2B–4B model like Qwen2.5/3.5).
* Meaning preservation and anti-hallucination test suite.

### Phase 9: Intelligent STT Router
* Benchmark-informed routing based on language, dictation length, accuracy requirements, and GPU memory pressure.

### Phase 10: JARVIS Assistant Mode v2
* Separate assistant hotkey (`Super + J`).
* Permission classification (`SAFE`, `SENSITIVE`, `DESTRUCTIVE`).
* Antigravity integration and quick local commands.

### Phase 11: Omarchy Product Integration
* Quickshell HUD integration (status, engine toggle, telemetry).
* CLI tools (`jarvis status`, `jarvis doctor`, `jarvis benchmark`).

### Phase 12: Public Linux Release
* Systemd user services, reproducible package setup, documentation, and troubleshooting guides.

---

## 5. Engineering Principles & Quality Targets
* **Hotkey Activation:** < 100ms p95.
* **First Useful Partial:** ~200–350ms (when streaming engine permits).
* **Final Insertion:** < 700–800ms p50 after speech release.
* **Supported-app Text Insertion Reliability:** > 99%.
* **Local Mode Network Calls:** 0 external transcription requests.
* **Trustworthiness First:** No fabricated benchmark numbers, no fake confidence values, no placeholder returns masquerading as actual transcripts.
