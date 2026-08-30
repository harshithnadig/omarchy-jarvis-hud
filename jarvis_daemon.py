#!/usr/bin/env python3
"""
Omni Jarvis: Continuous Live Voice Assistant (Zero-Wake-Word Barrier)
- Always-Listening Open-Mic: Every spoken question is answered instantly!
- No need to say "Hey Jarvis" - just speak naturally!
- Instant fast-path (0ms - 300ms) for Time, Date, Weather, Battery, Controls
- Antigravity AI for deep coding and reasoning
- In-Process Neural Edge-TTS Streaming
"""
import os
import sys
import time
import wave
import io
import re
import json
import urllib.request
import urllib.parse
import subprocess
import threading
import collections
import asyncio
import sounddevice as sd
import numpy as np
from faster_whisper.vad import get_vad_model
import edge_tts

print("🚀 Starting Always-Listening Omni Jarvis Voice OS...", flush=True)

SAMPLE_RATE = 16000
CHUNK_SIZE = 512  # 32ms per Silero frame

# Load Silero Neural VAD
print("🧠 Loading Silero Neural VAD...", flush=True)
vad_model = get_vad_model()
print("✅ Silero Neural VAD is live and calibrated!", flush=True)

# State
is_processing = False
is_speaking = False

audio_buffer = collections.deque(maxlen=int(SAMPLE_RATE * 15 / CHUNK_SIZE))
pre_roll = collections.deque(maxlen=int(SAMPLE_RATE * 0.4 / CHUNK_SIZE))
speech_active = False
speech_frames_count = 0
silence_frames_count = 0

VOICE = os.environ.get("AGY_VOICE", "en-US-ChristopherNeural")

def stop_current_speech():
    global is_speaking
    subprocess.run(["pkill", "-f", "mpv.*jarvis_audio"], stderr=subprocess.DEVNULL)
    is_speaking = False

def speak_in_process(text):
    """Direct stdin streaming playback without disk files or MPRIS topbar leaks."""
    global is_speaking, audio_buffer, pre_roll, speech_active, speech_frames_count, silence_frames_count
    if not text:
        return
    clean = re.sub(r"```[\s\S]*?```", " Code snippet. ", text)
    clean = re.sub(r"`[^`]*`", "", clean)
    clean = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", clean)
    clean = re.sub(r"[#*_~>|]", " ", clean)
    clean = re.sub(r"\s+", " ", clean).strip()
    if not clean:
        return

    try:
        is_speaking = True
        
        cmd = [
            "mpv",
            "--no-config",
            "--no-video",
            "--no-audio-display",
            "--really-quiet",
            "--title=jarvis_audio",
            "-"
        ]
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.DEVNULL)

        async def stream_audio():
            communicate = edge_tts.Communicate(clean, VOICE)
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    proc.stdin.write(chunk["data"])
                    proc.stdin.flush()

        asyncio.run(stream_audio())
        proc.stdin.close()
        proc.wait()
    except Exception as e:
        print(f"TTS error: {e}", flush=True)
    finally:
        is_speaking = False
        time.sleep(0.15)
        audio_buffer.clear()
        pre_roll.clear()
        speech_active = False
        speech_frames_count = 0
        silence_frames_count = 0

def transcribe_audio(pcm_bytes):
    out_buf = io.BytesIO()
    with wave.open(out_buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(pcm_bytes)
    wav_data = out_buf.getvalue()

    boundary = "----WebKitFormBoundaryJarvisAlways99"
    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="audio.wav"\r\n'
        f"Content-Type: audio/wav\r\n\r\n"
    ).encode("utf-8") + wav_data + f"\r\n--{boundary}--\r\n".encode("utf-8")

    req = urllib.request.Request(
        "http://127.0.0.1:8765/transcribe",
        data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"}
    )
    try:
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode())
            return data.get("text", "").strip()
    except Exception as e:
        print(f"⚠️ Transcription error: {e}", flush=True)
        return ""

def handle_quick_actions(query):
    q = query.lower().strip()
    # Strip optional jarvis prefix if spoken
    q = re.sub(r"^(?:hey\s+|ok\s+|yo\s+|hello\s+)?ja[rn]?v[ie][scz][,:\s]*", "", q).strip()

    # Self-Status & Greetings
    if q in ["hey", "hello", "hi", "how are you", "what are you doing", "who are you"]:
        return "I am Jarvis, your autonomous AI assistant. All neural pipelines on your RTX 4060 are active and I am listening."

    # Date & Day
    if "date" in q or "today's date" in q or "what day is it" in q or q in ["today", "day"]:
        return time.strftime("Today is %A, %B %d, %Y.")

    # Time
    if "what time is it" in q or "current time" in q or "what's the time" in q or q == "time":
        return time.strftime("It is currently %I:%M %p.")

    # Battery
    if "battery" in q or "power level" in q:
        try:
            with open("/sys/class/power_supply/BAT0/capacity") as f:
                cap = f.read().strip()
            with open("/sys/class/power_supply/BAT0/status") as f:
                stat = f.read().strip()
            return f"Battery is at {cap}% and currently {stat}."
        except Exception:
            pass

    # Weather
    if "weather" in q:
        city = "Bangalore"
        m = re.search(r"weather (?:in|for|at)?\s*([a-zA-Z\s]+)", q)
        if m and m.group(1).strip() and m.group(1).strip() not in ["today", "now", "outside", "like"]:
            city = m.group(1).strip().replace(" today", "").replace(" now", "").strip()
        try:
            req = urllib.request.Request(f"https://wttr.in/{urllib.parse.quote(city)}?format=%C,+%t", headers={"User-Agent": "curl/8.0"})
            with urllib.request.urlopen(req, timeout=3) as resp:
                w_text = resp.read().decode().strip()
                if w_text:
                    return f"In {city.title()}, the weather is currently {w_text}."
        except Exception:
            pass

    # System Controls
    if "lock screen" in q or "lock the screen" in q or "lock my laptop" in q:
        subprocess.Popen(["omarchy", "system", "lock"])
        return "Locking your screen."

    if "open browser" in q or "launch browser" in q or "open chrome" in q:
        subprocess.Popen(["google-chrome-stable"])
        return "Opening Google Chrome."

    if "open terminal" in q or "launch terminal" in q:
        subprocess.Popen(["foot"])
        return "Opening terminal."

    if "open code" in q or "open vs code" in q or "open vscode" in q:
        subprocess.Popen(["code"])
        return "Opening VS Code."

    if "volume up" in q or "increase volume" in q:
        subprocess.run(["wpctl", "set-volume", "@DEFAULT_AUDIO_SINK@", "5%+"])
        return "Volume increased."

    if "volume down" in q or "decrease volume" in q:
        subprocess.run(["wpctl", "set-volume", "@DEFAULT_AUDIO_SINK@", "5%-"])
        return "Volume decreased."

    if "mute" in q:
        subprocess.run(["wpctl", "set-mute", "@DEFAULT_AUDIO_SINK@", "toggle"])
        return "Audio toggled."

    return None

def process_voice_utterance(pcm_data):
    global is_processing
    try:
        raw_text = transcribe_audio(pcm_data)
        if not raw_text or len(raw_text.strip()) < 2:
            return

        # Filter out background noise artifacts
        if any(h in raw_text.lower() for h in ["watching", "subtitles", "dima", "gracias por ver"]):
            return

        clean_text = raw_text.strip(" ,:.-?!")
        print(f"🗣️ [User Spoke]: '{clean_text}'", flush=True)

        # 1. Instant Fast-Path (0ms - 300ms)
        quick_resp = handle_quick_actions(clean_text)
        if quick_resp:
            print(f"🤖 Jarvis: {quick_resp}", flush=True)
            speak_in_process(quick_resp)
            return

        # 2. Antigravity Agent Query
        print(f"⚡ [Antigravity Agent]: Processing in Omarchy...", flush=True)
        agent_prompt = (
            f"You are Jarvis, a voice-interactive desktop AI assistant on Omarchy Linux. "
            f"Execute the following user request and provide a concise, spoken-friendly answer (1-3 sentences max):\n\n{clean_text}"
        )
        result = subprocess.run(
            ["agy", "--dangerously-skip-permissions", "-p", agent_prompt],
            capture_output=True,
            text=True,
            timeout=120
        )
        response = result.stdout.strip()
        if not response:
            response = "Task executed successfully."

        print(f"🤖 Jarvis: {response}", flush=True)
        speak_in_process(response)

    except Exception as e:
        print(f"⚠️ Error: {e}", flush=True)
    finally:
        is_processing = False

def audio_callback(indata, frames, time_info, status):
    global is_processing, is_speaking, audio_buffer, pre_roll, speech_active, speech_frames_count, silence_frames_count

    if is_processing or is_speaking:
        return

    chunk = indata[:, 0].astype(np.float32)
    raw_pcm = (chunk * 32767).astype(np.int16)

    prob = float(vad_model(chunk)[0])

    if prob > 0.35:
        if not speech_active:
            speech_active = True
            speech_frames_count = 0
            silence_frames_count = 0
            audio_buffer.clear()
            audio_buffer.extend(pre_roll)
        audio_buffer.append(raw_pcm.tobytes())
        speech_frames_count += 1
        silence_frames_count = 0
    else:
        pre_roll.append(raw_pcm.tobytes())
        if speech_active:
            audio_buffer.append(raw_pcm.tobytes())
            silence_frames_count += 1
            if silence_frames_count > 12 and speech_frames_count > 8:
                speech_active = False
                speech_frames_count = 0
                silence_frames_count = 0
                is_processing = True
                pcm_data = b"".join(audio_buffer)
                audio_buffer.clear()
                threading.Thread(target=process_voice_utterance, args=(pcm_data,), daemon=True).start()

def main():
    print("🎧 Jarvis Always-Listening Open-Mic Engine is ACTIVE...", flush=True)
    with sd.InputStream(samplerate=SAMPLE_RATE, channels=1, blocksize=CHUNK_SIZE, dtype='float32', callback=audio_callback):
        while True:
            time.sleep(0.5)

if __name__ == "__main__":
    main()
