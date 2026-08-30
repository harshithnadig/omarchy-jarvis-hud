from .stt_engine import STTEngine
from faster_whisper import WhisperModel

class WhisperEngine(STTEngine):
    def __init__(self, model_name="large-v3-turbo", device="cuda", compute_type="float16"):
        self.model_name = model_name
        self.device = device
        self.compute_type = compute_type
        self.model = None

    def load_model(self):
        print(f"Loading WhisperEngine ({self.model_name}) on {self.device}...", flush=True)
        self.model = WhisperModel(self.model_name, device=self.device, compute_type=self.compute_type)
        print("WhisperEngine loaded.", flush=True)

    def transcribe_batch(self, audio_path: str, **kwargs) -> str:
        segments, _ = self.model.transcribe(
            audio_path,
            vad_filter=True,
            vad_parameters=dict(min_silence_duration_ms=500, speech_pad_ms=400),
            **kwargs
        )
        return " ".join([s.text.strip() for s in segments]).strip()

    def transcribe_stream(self, audio_stream, **kwargs):
        """Whisper doesn't natively stream well, this is a placeholder for chunked fallback."""
        raise NotImplementedError("WhisperEngine does not support true cache-aware streaming.")
