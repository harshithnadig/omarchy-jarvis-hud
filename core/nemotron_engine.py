import os
import time
import wave
import contextlib
from typing import Optional
from .stt_engine import (
    STTEngine,
    TranscriptionResult,
    EngineUnavailableError,
    ModelLoadError,
    InferenceError,
)

class NemotronEngine(STTEngine):
    """
    NVIDIA NeMo ASR Engine wrapper.
    Target models: nvidia/nemotron-speech-streaming-en-0.6b or FastConformer models.
    Note: Full cache-aware chunk streaming API is targeted for Phase 4.
    """
    def __init__(self, model_id: str = "nvidia/nemotron-speech-streaming-en-0.6b"):
        super().__init__(name=f"nemotron-{model_id.split('/')[-1]}")
        self.model_id = model_id
        self.model = None

    def is_available(self) -> bool:
        """Check if nemo.collections.asr is importable in the active environment."""
        try:
            import nemo.collections.asr as _nemo_asr  # noqa: F401
            return True
        except ImportError:
            return False

    def _get_audio_duration(self, audio_path: str) -> float:
        try:
            with contextlib.closing(wave.open(audio_path, 'r')) as f:
                frames = f.getnframes()
                rate = f.getframerate()
                return frames / float(rate)
        except Exception:
            return 0.0

    def load_model(self, device: str = "cuda", compute_type: str = "float16"):
        if not self.is_available():
            self.is_loaded = False
            raise EngineUnavailableError(
                f"NVIDIA NeMo toolkit is not installed. Cannot load '{self.model_id}'. "
                "Install NeMo ASR in your environment or use a Whisper engine."
            )

        print(f"📦 [NemotronEngine] Loading pretrained model '{self.model_id}' on {device}...", flush=True)
        try:
            import nemo.collections.asr as nemo_asr
            self.model = nemo_asr.models.ASRModel.from_pretrained(model_name=self.model_id)
            if device == "cuda":
                self.model = self.model.cuda()
            self.is_loaded = True
            print(f"✅ [NemotronEngine] Model '{self.model_id}' loaded successfully.", flush=True)
        except Exception as e:
            self.is_loaded = False
            raise ModelLoadError(f"Failed to load Nemotron model '{self.model_id}': {e}") from e

    def transcribe_file(
        self,
        audio_path: str,
        language: Optional[str] = None,
        hotwords: Optional[str] = None,
        **kwargs
    ) -> TranscriptionResult:
        if not os.path.exists(audio_path):
            raise InferenceError(f"Audio file not found: {audio_path}")

        if not self.is_loaded or self.model is None:
            self.load_model()

        audio_duration = self._get_audio_duration(audio_path)
        start_time = time.perf_counter()

        try:
            transcriptions = self.model.transcribe([audio_path])
            if isinstance(transcriptions, list) and len(transcriptions) > 0:
                text = transcriptions[0]
                if hasattr(text, "text"):
                    text = text.text
                else:
                    text = str(text)
            else:
                text = str(transcriptions)
        except Exception as e:
            raise InferenceError(f"Nemotron inference failed: {e}") from e

        elapsed_sec = time.perf_counter() - start_time
        latency_ms = elapsed_sec * 1000.0
        rtf = (elapsed_sec / audio_duration) if audio_duration > 0 else 0.0

        return TranscriptionResult(
            text=text.strip(),
            language="en",
            confidence=None,  # NeMo batch transcribe does not provide calibrated confidence
            latency_ms=round(latency_ms, 2),
            audio_duration_s=round(audio_duration, 2),
            rtf=round(rtf, 3),
            engine_name=self.name,
            metadata={"model_id": self.model_id}
        )

    def streaming_step(self, pcm_chunk: bytes, cache_state: Optional[dict] = None) -> tuple[str, dict]:
        """
        Execute an incremental cache-aware streaming inference step on a 160ms PCM chunk.
        Reuses encoder cache tensors to eliminate quadratic O(N^2) buffer recomputation.
        """
        if not self.is_available():
            raise EngineUnavailableError("NVIDIA NeMo toolkit is not installed.")

        if not self.is_loaded or self.model is None:
            self.load_model()

        import numpy as np
        import torch

        # Normalize 16-bit PCM to float32 [-1.0, 1.0]
        samples = np.frombuffer(pcm_chunk, dtype=np.int16).astype(np.float32) / 32768.0
        audio_tensor = torch.from_numpy(samples).unsqueeze(0)
        if torch.cuda.is_available() and self.is_loaded:
            audio_tensor = audio_tensor.cuda()

        state = cache_state or {}
        text = ""

        # NeMo Cache-Aware Streaming Execution
        try:
            if hasattr(self.model, "streaming_step"):
                text, new_cache = self.model.streaming_step(audio_tensor, state)
                return text, new_cache
            elif hasattr(self.model, "transcribe"):
                # Fallback step for non-streaming checkpoints
                res = self.model.transcribe([audio_tensor.cpu().numpy()])[0]
                text = res.text if hasattr(res, "text") else str(res)
                return text, state
        except Exception as e:
            raise InferenceError(f"Nemotron streaming step failed: {e}") from e

        return text, state
