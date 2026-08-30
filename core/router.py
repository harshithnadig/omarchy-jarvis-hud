from typing import Dict, Optional, List, Any
from .stt_engine import STTEngine, TranscriptionResult
from .whisper_engine import WhisperEngine
from .nemotron_engine import NemotronEngine

class EngineRouter:
    """
    Multi-Engine Orchestrator:
    - turbo: Whisper Large-v3-Turbo (Fast, balanced multilingual)
    - large-v3: Whisper Large-v3 (Maximum multilingual & accent accuracy)
    - nemotron: NVIDIA Nemotron Streaming 0.6B (Cache-aware live streaming)
    """
    def __init__(self, default_engine: str = "turbo"):
        self.default_engine_key = default_engine
        self._engines: Dict[str, STTEngine] = {
            "turbo": WhisperEngine(model_id="large-v3-turbo", compute_type="float16"),
            "large-v3": WhisperEngine(model_id="large-v3", compute_type="float16"),
            "nemotron": NemotronEngine(model_id="nvidia/nemotron-speech-streaming-en-0.6b"),
        }
        self.active_engine_key = default_engine

    def get_engine(self, engine_key: Optional[str] = None) -> STTEngine:
        key = (engine_key or self.active_engine_key).lower().strip()
        if key in ("whisper", "default", "auto"):
            key = self.active_engine_key
        if key not in self._engines:
            print(f"⚠️ [EngineRouter] Unknown engine '{key}', falling back to '{self.default_engine_key}'", flush=True)
            key = self.default_engine_key
        return self._engines[key]

    def set_default_engine(self, engine_key: str):
        key = engine_key.lower().strip()
        if key in self._engines:
            self.active_engine_key = key
            print(f"🔀 [EngineRouter] Active engine switched to: '{key}'", flush=True)
        else:
            raise ValueError(f"Unknown engine '{key}'. Available: {list(self._engines.keys())}")

    def list_engines(self) -> List[Dict[str, Any]]:
        result = []
        for key, eng in self._engines.items():
            result.append({
                "key": key,
                "name": eng.name,
                "is_loaded": eng.is_loaded,
                "is_active": (key == self.active_engine_key)
            })
        return result

    def transcribe(
        self,
        audio_path: str,
        engine_key: Optional[str] = None,
        language: Optional[str] = None,
        hotwords: Optional[str] = None,
        **kwargs
    ) -> TranscriptionResult:
        engine = self.get_engine(engine_key)
        return engine.transcribe_file(
            audio_path=audio_path,
            language=language,
            hotwords=hotwords,
            **kwargs
        )
