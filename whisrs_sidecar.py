#!/usr/bin/env python3
import os
import tempfile
from fastapi import FastAPI, UploadFile, File, Form
from core.whisper_engine import WhisperEngine
from core.nemotron_engine import NemotronEngine

app = FastAPI(title="JARVIS Voice OS")

# Phase 1: Abstraction achieved.
# Currently loading Whisper as default until Nemotron benchmark passes.
engine = WhisperEngine(model_name="large-v3-turbo", compute_type="float16")
engine.load_model()

@app.post("/transcribe")
async def transcribe(file: UploadFile = File(...)):
    raw_content = await file.read()
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        tmp.write(raw_content)
        tmp_path = tmp.name

    try:
        final_text = engine.transcribe_batch(tmp_path)
        print(f"🎙️ [Master Output]: {final_text}", flush=True)
        return {"text": final_text}
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
