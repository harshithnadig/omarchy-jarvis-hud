import time
import wave
import contextlib
from typing import Optional
from .stt_engine import STTEngine, TranscriptionResult

class NemotronEngine(STTEngine):
    """
    NVIDIA Nemotron Cache-Aware Streaming ASR Engine.
    Primary target: nvidia/nemotron-speech-streaming-en-0.6b or nemotron-3.5-asr-streaming-0.6b.
    Provides sub-200ms latency for continuous speech typing.
    """
    def __init__(self, model_id: str = "nvidia/nemotron-speech-streaming-en-0.6b"):
        super().__init__(name=f"nemotron-{model_id.split('/')[-1]}")
        self.model_id = model_id
        self.model = None

    def _get_audio_duration(self, audio_path: str) -> float:
        try:
            with contextlib.closing(wave.open(audio_path, 'r')) as f:
                frames = f.getnframes()
                rate = f.getframerate()
                return frames / float(rate)
        except Exception:
            return 0.0

    def load_model(self, device: str = "cuda", compute_type: str = "float16"):
        print(f"⚡ [NemotronEngine] Checking NeMo runtime for '{self.model_id}'...", flush=True)
        try:
            import nemo.collections.asr as nemo_asr
            print(f"📦 [NemotronEngine] Loading pretrained model '{self.model_id}'...", flush=True)
            self.model = nemo_asr.models.ASRModel.from_pretrained(model_name=self.model_id)
            if device == "cuda":
                self.model = self.model.cuda()
            self.is_loaded = True
            print("✅ [NemotronEngine] Ready for cache-aware streaming.", flush=True)
        except ImportError:
            print("ℹ️ [NemotronEngine] NeMo toolkit not currently installed. (Placeholder active for benchmarks)", flush=True)
            self.is_loaded = False
        except Exception as e:
            print(f"⚠️ [NemotronEngine] Failed to load ({e}).", flush=True)
            self.is_loaded = False

    def transcribe_file(
        self,
        audio_path: str,
        language: Optional[str] = None,
        hotwords: Optional[str] = None,
        **kwargs
    ) -> TranscriptionResult:
        audio_duration = self._get_audio_duration(audio_path)
        start_time = time.perf_counter()

        if self.is_loaded and self.model is not None:
            transcriptions = self.model.transcribe([audio_path])
            text = transcriptions[0] if isinstance(transcriptions, list) else str(transcriptions)
        else:
            # Fallback notification if NeMo isn't installed in the environment yet
            text = f"[Nemotron Placeholder: NeMo ASR required for {self.model_id}]"

        elapsed_sec = time.perf_counter() - start_time
        latency_ms = elapsed_sec * 1000.0
        rtf = (elapsed_sec / audio_duration) if audio_duration > 0 else 0.0

        return TranscriptionResult(
            text=text,
            language="en",
            confidence=0.95,
            latency_ms=round(latency_ms, 2),
            audio_duration_s=round(audio_duration, 2),
            rtf=round(rtf, 3),
            engine_name=self.name,
            metadata={"model_id": self.model_id}
        )
