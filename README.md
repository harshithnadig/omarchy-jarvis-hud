# Omni Jarvis HUD

A lightning-fast, highly accurate voice assistant built for the Omarchy OS ecosystem. It bypasses standard cloud API limits (like the 25MB Whisper limit) by running a persistent, highly-optimized transcription server natively on your GPU.

## The Architecture (The "Idea")

This repository consists of a triad of scripts designed to eliminate the "Cold Start" delay of AI models and prevent audio hallucinations.

### 1. The Hot Server (`whisrs_sidecar.py`)
This is the core engine. It runs persistently in the background on port `8765`. 
* **Turbo Engine:** Uses OpenAI's latest `large-v3-turbo` model for dictation that is identical in accuracy to the flagship model but 4x-8x faster.
* **VAD (Voice Activity Detection):** Uses Silero VAD (`vad_filter=True` with `500ms` padding) to mathematically cut out silence before inference. This prevents the model from hallucinating text during silent pauses and allows infinite-length audio processing.
* **VRAM Optimization:** Uses `int8_float16` quantization via `faster-whisper` to cut VRAM usage in half, allowing it to run smoothly on an RTX 4060 alongside other coding models (like Ollama).

### 2. The Push-To-Talk Client (`jarvis-ptt`)
Bound to `Super+H`. When triggered, it records your microphone, instantly shoots the audio to the local sidecar server, and receives the transcription.

### 3. The Always-Listening Daemon (`jarvis_daemon.py`)
An open-mic, zero-wake-word implementation. It listens continuously to the microphone, uses VAD to detect when you actually speak (ignoring background noise), and processes queries dynamically.
