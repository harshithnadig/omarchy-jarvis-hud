#!/usr/bin/env python3
import os
import sys
import re
import json
import subprocess
import tempfile
import uvicorn
from fastapi import FastAPI, UploadFile, File, Form

# Prepend NVIDIA CUDA and cuDNN libraries to LD_LIBRARY_PATH
try:
    import nvidia.cublas.lib
    import nvidia.cudnn.lib
    os.environ['LD_LIBRARY_PATH'] = f"{nvidia.cublas.lib.__path__[0]}:{nvidia.cudnn.lib.__path__[0]}:" + os.environ.get('LD_LIBRARY_PATH', '')
except ImportError:
    pass

from faster_whisper import WhisperModel

app = FastAPI(title="Master Multi-Repo AI Dictation Engine - NVIDIA GPU")

print("🚀 Loading Whisper Large-v3 (1.55 Billion Flagship Model) on NVIDIA RTX 4060 GPU...", flush=True)
model = WhisperModel(
    "large-v3-turbo",
    device="cuda",
    compute_type="float16"
)
print("✅ Flagship Model & Ultra-Robust Intelligence Pipeline is LIVE on port 8765!", flush=True)

HOTWORDS = (
    "Hyprland, Omarchy, Linux, Arch, Python, GitHub, API, Rust, CLI, VSCode, Chrome, "
    "Discord, bash, terminal, function, variable, import, export, return, async, await, "
    "Docker, Kubernetes, React, TypeScript, JavaScript, SQL, Postgres, Git, commit, "
    "push, pull, merge, branch, PR, Claude, ChatGPT, Gemini, AI, prompt, model, "
    "camelCase, snake_case, kebab-case, PascalCase, screaming_snake_case, fat arrow"
)

CODE_OPS = {
    r"\b(?:fat arrow|fat error|fed arrow|fat aero)\b": "=>",
    r"\b(?:thin arrow|thin error)\b": "->",
    r"\b(?:arrow function)\b": "() => {}",
    r"\b(?:triple equals|triple equal)\b": "===",
    r"\b(?:not double equals|not double equal)\b": "!==",
    r"\b(?:double equals|double equal)\b": "==",
    r"\b(?:not equals|not equal)\b": "!=",
    r"\b(?:plus equals|plus equal)\b": "+=",
    r"\b(?:minus equals|minus equal)\b": "-=",
    r"\b(?:times equals|times equal)\b": "*=",
    r"\b(?:divided by equals)\b": "/=",
    r"\b(?:plus plus)\b": "++",
    r"\b(?:minus minus)\b": "--",
    r"\b(?:logical and)\b": "&&",
    r"\b(?:logical or)\b": "||",
    r"\b(?:nullish coalescing)\b": "??",
    r"\b(?:optional chaining)\b": "?.",
    r"\b(?:scope resolution)\b": "::",
    r"\b(?:git commit)\b": "git commit -m \"\"",
    r"\b(?:git push)\b": "git push",
    r"\b(?:git pull)\b": "git pull",
    r"\b(?:console log)\b": "console.log()",
    r"\b(?:print statement)\b": "print()",
}

PUNCT_MAP = {
    r"\b(?:new line|newline)\b": "\n",
    r"\b(?:new paragraph|newparagraph)\b": "\n\n",
    r"\b(?:period|full stop|fullstop)\b": ".",
    r"\b(?:comma)\b": ",",
    r"\b(?:question mark|questionmark)\b": "?",
    r"\b(?:exclamation mark|exclamationmark|exclamation point)\b": "!",
    r"\b(?:colon)\b": ":",
    r"\b(?:semicolon)\b": ";",
    r"\b(?:ellipsis|dot dot dot)\b": "...",
    r"\b(?:em dash)\b": " — ",
    r"\b(?:open paren|open parenthesis)\b": "(",
    r"\b(?:close paren|close parenthesis)\b": ")",
    r"\b(?:open bracket|open square bracket)\b": "[",
    r"\b(?:close bracket|close square bracket)\b": "]",
    r"\b(?:open brace|open curly brace)\b": "{",
    r"\b(?:close brace|close curly brace)\b": "}",
    r"\b(?:open quote|open quotes)\b": "\"",
    r"\b(?:close quote|close quotes)\b": "\"",
    r"\b(?:single quote|open single quote|close single quote)\b": "'",
    r"\b(?:at sign)\b": "@",
    r"\b(?:hashtag)\b": "#",
    r"\b(?:dollar sign)\b": "$",
    r"\b(?:percent sign)\b": "%",
    r"\b(?:forward slash)\b": "/",
    r"\b(?:backslash)\b": "\\",
    r"\b(?:underscore)\b": "_",
    r"\b(?:dash)\b": "-",
}

EMOJI_BASE = {
    "fire": "🔥", "flame": "🔥", "rocket": "🚀", "skull": "💀",
    "laughing": "😂", "laugh": "😂", "lol": "😂", "heart": "❤️",
    "red heart": "❤️", "thumbs up": "👍", "thumbs down": "👎",
    "check mark": "✅", "checkmark": "✅", "cross mark": "❌",
    "100": "💯", "hundred": "💯", "sparkles": "✨", "sparkle": "✨",
    "eyes": "👀", "party": "🎉", "celebration": "🎉", "clap": "👏",
    "clapping": "👏", "mind blown": "🤯", "thinking": "🤔",
    "sunglasses": "😎", "cool": "😎", "crying": "😭", "sob": "😭",
    "pray": "🙏", "praying": "🙏", "star": "⭐", "poop": "💩",
}

NUM_MAP = {
    "two": 2, "three": 3, "four": 4, "five": 5, "six": 6,
    "2": 2, "3": 3, "4": 4, "5": 5, "6": 6
}

DIRECT_EMOJIS = {
    "thumbs up": "👍", "thumbs down": "👎", "check mark": "✅",
    "cross mark": "❌", "mind blown": "🤯", "shrug": "¯\\_(ツ)_/¯"
}

def expand_all_emojis(text: str) -> str:
    # 1. Numbered repetitions: "three fire emojis" -> "🔥🔥🔥"
    for num_word, count in NUM_MAP.items():
        for name, emoji in EMOJI_BASE.items():
            pattern = re.compile(rf"\b{num_word}\s+{re.escape(name)}\s*emojis?\b", re.IGNORECASE)
            text = pattern.sub(emoji * count, text)

    # 2. Singular / plural: "fire emoji", "fire emojis", "fireemoji"
    for name, emoji in sorted(EMOJI_BASE.items(), key=lambda x: len(x[0]), reverse=True):
        pattern = re.compile(rf"\b{re.escape(name)}\s*emojis?\b", re.IGNORECASE)
        text = pattern.sub(emoji, text)

    # 3. Direct idiomatic triggers
    for phrase, symbol in DIRECT_EMOJIS.items():
        text = re.sub(rf"\b{re.escape(phrase)}\b", lambda m, s=symbol: s, text, flags=re.IGNORECASE)

    return text

def master_polish(text: str) -> str:
    if not text:
        return ""

    try:
        # 1. Anti-Hallucination: Collapse runaway repeating syllables
        text = re.sub(r"([a-zA-Z]{1,4})\1{2,}", r"\1", text)

        # 2. Clean Stutters & Duplicated words
        text = re.sub(r"\b([a-zA-Z]+)\s+\1\b", r"\1", text, flags=re.IGNORECASE)

        # 3. Filler words removal
        text = re.sub(r"\b(um|uh|erm|er|ah|ahh)\b", "", text, flags=re.IGNORECASE)

        # 4. Self-Correction & Backtracking (e.g. "wait no, actually 20")
        if re.search(r"\b(actually|wait no|scratch that|no wait)\b", text, re.IGNORECASE):
            text = re.sub(r"^.*?\b(?:actually|wait no|scratch that|no wait),?\s*", "", text, flags=re.IGNORECASE)

        # 5. Developer Code Operators (fat arrow -> =>, etc.)
        for pat, sym in CODE_OPS.items():
            text = re.sub(pat, lambda m, s=sym: s, text, flags=re.IGNORECASE)

        # 6. Spoken Punctuation & Layout
        for pat, sym in PUNCT_MAP.items():
            text = re.sub(pat, lambda m, s=sym: s, text, flags=re.IGNORECASE)

        # 7. Emojis
        text = expand_all_emojis(text)

        # 8. Robust Developer Casing Transforms
        def apply_case(m):
            mode = m.group(1).lower()
            words = re.findall(r"[a-zA-Z0-9]+", m.group(2))
            if not words:
                return ""
            if mode == "camel":
                res = words[0].lower() + "".join(w.capitalize() for w in words[1:])
            elif mode == "snake":
                res = "_".join(w.lower() for w in words)
            elif mode == "kebab":
                res = "-".join(w.lower() for w in words)
            elif mode == "pascal":
                res = "".join(w.capitalize() for w in words)
            elif mode == "constant":
                res = "_".join(w.upper() for w in words)
            else:
                res = " ".join(words)
            return res + " "

        text = re.sub(
            r"\b(camel|snake|kebab|pascal|constant)\s*case[,\s:]+([a-zA-Z0-9\s]+?)(?=(?:\b(?:camel|snake|kebab|pascal|constant)\s*case|[.,!?;:\n]|$))",
            apply_case,
            text,
            flags=re.IGNORECASE
        )

        # 9. Numbers, Currency & Units
        text = re.sub(r"\b(\d+)\s+dollars?\b", r"$\1", text, flags=re.IGNORECASE)
        text = re.sub(r"\b(\d+)\s+percent\b", r"\1%", text, flags=re.IGNORECASE)
        text = re.sub(r"\b(\d+)\s+(megabytes?|mb)\b", r"\1 MB", text, flags=re.IGNORECASE)
        text = re.sub(r"\b(\d+)\s+(gigabytes?|gb)\b", r"\1 GB", text, flags=re.IGNORECASE)
        text = re.sub(r"\b(\d+)\s+(milliseconds?|ms)\b", r"\1 ms", text, flags=re.IGNORECASE)

        # 10. Clean Stacked Punctuation & Trailing Commas
        text = re.sub(r"[,]+", ",", text)
        text = re.sub(r"\.+", ".", text)
        text = re.sub(r"([.,!?:;])\s*[,.]+", r"\1", text)
        text = re.sub(r"[,]+\s*([.!?\n])", r"\1", text)
        text = re.sub(r"\s+([.,!?:;])", r"\1", text)
        text = re.sub(r"([(\[{])\s+", r"\1", text)
        text = re.sub(r"\s+([)\]}])", r"\1", text)
        text = re.sub(r" +", " ", text)
        text = re.sub(r"(^|[.!?\n]\s*)([a-z])", lambda m: m.group(1) + m.group(2).upper(), text.strip())
    except Exception as e:
        print(f"⚠️ Polish error: {e}", flush=True)

    return text

@app.post("/transcribe")
async def transcribe(
    file: UploadFile = File(...),
    model_name: str = Form(default="large-v3-turbo"),
    language: str = Form(default=None),
    hotwords: str = Form(default=None)
):
    raw_content = await file.read()
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        tmp.write(raw_content)
        tmp_path = tmp.name

    try:
        target_lang = "en"
        if language and language.strip() and language.strip().lower() not in ["auto", "none", "null"]:
            target_lang = language.strip().lower()

        combined_hotwords = f"{HOTWORDS}, {hotwords}" if hotwords else HOTWORDS

        segments, info = model.transcribe(
            tmp_path,
            language=target_lang,
            task="transcribe",
            beam_size=5,
            best_of=5,
            temperature=0.0,
            compression_ratio_threshold=2.4,
            condition_on_previous_text=False,
            vad_filter=True,
            vad_parameters=dict(min_silence_duration_ms=500, speech_pad_ms=400),
            hotwords=combined_hotwords
        )
        
        raw_text = " ".join([s.text.strip() for s in segments]).strip()
        final_text = master_polish(raw_text)
        
        if final_text:
            print(f"🎙️ [Master Output]: {final_text}", flush=True)
        else:
            print("⚠️ [Master Engine]: No speech detected.", flush=True)
            
        return {"text": final_text}
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8765, log_level="warning")
