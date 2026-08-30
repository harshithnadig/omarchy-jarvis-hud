import time
import wave
import contextlib
from typing import Optional
from .stt_engine import STTEngine, TranscriptionResult

class WhisperEngine(STTEngine):
    """
    High-performance Whisper Engine using CTranslate2 (faster-whisper).
    Supports: large-v3, large-v3-turbo, medium, small, base.
    """
    def __init__(
        self,
        model_id: str = "large-v3-turbo",
        device: str = "cuda",
        compute_type: str = "float16",
        min_silence_duration_ms: int = 500,
        speech_pad_ms: int = 400,
    ):
        super().__init__(name=f"whisper-{model_id}")
        self.model_id = model_id
        self.device = device
        self.compute_type = compute_type
        self.min_silence_duration_ms = min_silence_duration_ms
        self.speech_pad_ms = speech_pad_ms
        self.model = None

    def _get_audio_duration(self, audio_path: str) -> float:
        try:
            with contextlib.closing(wave.open(audio_path, 'r')) as f:
                frames = f.getnframes()
                rate = f.getframerate()
                return frames / float(rate)
        except Exception:
            return 0.0

    def load_model(self, device: Optional[str] = None, compute_type: Optional[str] = None):
        from faster_whisper import WhisperModel

        dev = device or self.device
        ct = compute_type or self.compute_type

        print(f"⚡ [WhisperEngine] Loading '{self.model_id}' on {dev} ({ct})...", flush=True)
        try:
            self.model = WhisperModel(self.model_id, device=dev, compute_type=ct)
            self.is_loaded = True
            print(f"✅ [WhisperEngine] '{self.model_id}' is LIVE in memory.", flush=True)
        except Exception as e:
            if dev == "cuda":
                print(f"⚠️ [WhisperEngine] CUDA failed ({e}), falling back to CPU...", flush=True)
                self.model = WhisperModel(self.model_id, device="cpu", compute_type="int8")
                self.device = "cpu"
                self.compute_type = "int8"
                self.is_loaded = True
            else:
                raise e

    def transcribe_file(
        self,
        audio_path: str,
        language: Optional[str] = None,
        hotwords: Optional[str] = None,
        beam_size: int = 5,
        **kwargs
    ) -> TranscriptionResult:
        if not self.is_loaded or self.model is None:
            self.load_model()

        audio_duration = self._get_audio_duration(audio_path)
        start_time = time.perf_counter()

        target_lang = None
        if language and language.strip().lower() not in ("auto", "none", "null", ""):
            target_lang = language.strip().lower()

        segments, info = self.model.transcribe(
            audio_path,
            language=target_lang,
            task="transcribe",
            beam_size=beam_size,
            best_of=beam_size,
            temperature=0.0,
            compression_ratio_threshold=2.4,
            condition_on_previous_text=False,
            vad_filter=True,
            vad_parameters=dict(
                min_silence_duration_ms=self.min_silence_duration_ms,
                speech_pad_ms=self.speech_pad_ms
            ),
            hotwords=hotwords
        )

        texts = []
        for s in segments:
            texts.append(s.text.strip())

        final_text = " ".join(texts).strip()
        elapsed_sec = time.perf_counter() - start_time
        latency_ms = elapsed_sec * 1000.0
        rtf = (elapsed_sec / audio_duration) if audio_duration > 0 else 0.0

        return TranscriptionResult(
            text=final_text,
            language=info.language,
            confidence=float(info.language_probability),
            latency_ms=round(latency_ms, 2),
            audio_duration_s=round(audio_duration, 2),
            rtf=round(rtf, 3),
            engine_name=self.name,
            metadata={
                "model_id": self.model_id,
                "compute_type": self.compute_type,
                "device": self.device
            }
        )
