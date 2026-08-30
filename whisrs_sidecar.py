#!/usr/bin/env python3
import os
import tempfile
from fastapi import FastAPI, UploadFile, File, Form, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from core.router import EngineRouter
from core.stt_engine import STTError, EngineUnavailableError
from core.polisher import TextPolisher

app = FastAPI(title="JARVIS Multi-Engine Voice Sidecar")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Multi-Engine Router with Turbo as default
router = EngineRouter(default_engine="turbo")

# Preload default engine if available
try:
    default_eng = router.get_engine()
    if default_eng.is_available():
        default_eng.load_model()
except Exception as e:
    print(f"⚠️ [Sidecar Startup] Could not preload default engine: {e}", flush=True)

@app.get("/health")
def health():
    return {
        "status": "ONLINE",
        "active_engine": router.active_engine_key,
        "engines": router.list_engines()
    }

@app.get("/engines")
def list_engines():
    return {"engines": router.list_engines()}

@app.post("/engine/switch")
def switch_engine(key: str = Query(..., description="Engine key: turbo, large-v3, nemotron")):
    try:
        router.set_default_engine(key)
        # Pre-load on switch
        eng = router.get_engine()
        if not eng.is_loaded:
            eng.load_model()
        return {"status": "success", "active_engine": router.active_engine_key}
    except (ValueError, STTError) as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/transcribe")
async def transcribe(
    file: UploadFile = File(...),
    engine: str = Query(default=None, description="Optional override engine: turbo, large-v3, nemotron"),
    language: str = Form(default=None),
    hotwords: str = Form(default=None),
    raw: bool = Query(default=False, description="Bypass polishing if True")
):
    raw_content = await file.read()
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        tmp.write(raw_content)
        tmp_path = tmp.name

    try:
        # Run transcription via multi-engine router
        result = router.transcribe(
            audio_path=tmp_path,
            engine_key=engine,
            language=language,
            hotwords=hotwords
        )

        # Apply safe deterministic polish unless raw is requested
        final_text = result.text if raw else TextPolisher.clean_deterministic(result.text)

        print(f"🎙️ [{result.engine_name}] ({result.latency_ms}ms | RTF: {result.rtf}x): {final_text}", flush=True)

        return {
            "text": final_text,
            "raw_text": result.text,
            "language": result.language,
            "confidence": result.confidence,
            "latency_ms": result.latency_ms,
            "audio_duration_s": result.audio_duration_s,
            "rtf": result.rtf,
            "engine": result.engine_name
        }
    except EngineUnavailableError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except STTError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Transcription failure: {e}")
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8765)

