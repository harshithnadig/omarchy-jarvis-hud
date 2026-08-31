import os
import gc
import sys
import site
import ctypes
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

_CUDA_LIBS_INITIALIZED = False

def ensure_cuda_libraries():
    """Dynamically pre-load nvidia cublas & cudnn shared libraries if installed in python site-packages."""
    global _CUDA_LIBS_INITIALIZED
    if _CUDA_LIBS_INITIALIZED:
        return

    try:
        for p in site.getsitepackages():
            cublas_dir = os.path.join(p, 'nvidia', 'cublas', 'lib')
            cudnn_dir = os.path.join(p, 'nvidia', 'cudnn', 'lib')
            for d in (cublas_dir, cudnn_dir):
                if os.path.exists(d):
                    # Set LD_LIBRARY_PATH environment in current process
                    cur_ld = os.environ.get("LD_LIBRARY_PATH", "")
                    if d not in cur_ld:
                        os.environ["LD_LIBRARY_PATH"] = f"{d}:{cur_ld}" if cur_ld else d
                    # Pre-load shared objects into process memory
                    for f in sorted(os.listdir(d)):
                        if f.endswith('.so') or '.so.' in f:
                            try:
                                ctypes.CDLL(os.path.join(d, f))
                            except Exception:
                                pass
    except Exception:
        pass
    _CUDA_LIBS_INITIALIZED = True


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

    def is_available(self) -> bool:
        """Check if faster-whisper is installed."""
        try:
            import faster_whisper  # noqa: F401
            return True
        except ImportError:
            return False

    def _get_audio_duration(self, audio_path: str) -> float:
        # Try PyAV for universal container support (mp3, wav, flac, ogg, etc.)
        try:
            import av
            with av.open(audio_path) as container:
                if container.duration is not None:
                    return float(container.duration) / av.time_base
        except Exception:
            pass

        # Fallback to standard wave reader
        try:
            with contextlib.closing(wave.open(audio_path, 'r')) as f:
                frames = f.getnframes()
                rate = f.getframerate()
                return frames / float(rate)
        except Exception:
            return 0.0

    def load_model(self, device: Optional[str] = None, compute_type: Optional[str] = None):
        if not self.is_available():
            self.is_loaded = False
            raise EngineUnavailableError("faster-whisper is not installed in the active environment.")

        dev = device or self.device
        ct = compute_type or self.compute_type

        if dev == "cuda":
            ensure_cuda_libraries()

        from faster_whisper import WhisperModel

        print(f"⚡ [WhisperEngine] Loading '{self.model_id}' on {dev} ({ct})...", flush=True)
        try:
            self.model = WhisperModel(self.model_id, device=dev, compute_type=ct)
            self.is_loaded = True
            self.device = dev
            self.compute_type = ct
            print(f"✅ [WhisperEngine] '{self.model_id}' is LIVE in memory.", flush=True)
        except Exception as e:
            if dev == "cuda":
                print(f"⚠️ [WhisperEngine] CUDA failed ({e}), falling back to CPU...", flush=True)
                try:
                    self.model = WhisperModel(self.model_id, device="cpu", compute_type="int8")
                    self.device = "cpu"
                    self.compute_type = "int8"
                    self.is_loaded = True
                except Exception as cpu_err:
                    self.is_loaded = False
                    raise ModelLoadError(f"Failed to load Whisper on both CUDA and CPU: {cpu_err}") from cpu_err
            else:
                self.is_loaded = False
                raise ModelLoadError(f"Failed to load Whisper model '{self.model_id}': {e}") from e

    def unload_model(self):
        """Free model weights from VRAM/RAM."""
        if self.model is not None:
            del self.model
            self.model = None
            gc.collect()
        self.is_loaded = False
        print(f"🧹 [WhisperEngine] '{self.model_id}' unloaded from memory.", flush=True)

    def transcribe_file(
        self,
        audio_path: str,
        language: Optional[str] = None,
        hotwords: Optional[str] = None,
        beam_size: int = 5,
        **kwargs
    ) -> TranscriptionResult:
        if not os.path.exists(audio_path):
            raise InferenceError(f"Audio file not found: {audio_path}")

        if not self.is_loaded or self.model is None:
            self.load_model()

        audio_duration = self._get_audio_duration(audio_path)
        start_time = time.perf_counter()

        target_lang = None
        if language and language.strip().lower() not in ("auto", "none", "null", ""):
            target_lang = language.strip().lower()

        try:
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

            texts = [s.text.strip() for s in segments]
            final_text = " ".join(texts).strip()
        except Exception as e:
            raise InferenceError(f"Whisper transcription failed: {e}") from e

        elapsed_sec = time.perf_counter() - start_time
        latency_ms = elapsed_sec * 1000.0
        rtf = (elapsed_sec / audio_duration) if audio_duration > 0 else 0.0

        return TranscriptionResult(
            text=final_text,
            language=info.language,
            confidence=float(info.language_probability) if hasattr(info, "language_probability") else None,
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

    def streaming_step(self, pcm_chunk: bytes, cache_state: Optional[dict] = None) -> tuple[str, dict]:
        """
        Incremental streaming decode step on a 160ms PCM chunk without saving temporary WAV files to disk.
        """
        if not self.is_available():
            raise EngineUnavailableError("faster-whisper is not installed.")

        if not self.is_loaded or self.model is None:
            self.load_model()

        import numpy as np

        state = cache_state or {}
        samples = np.frombuffer(pcm_chunk, dtype=np.int16).astype(np.float32) / 32768.0

        if "accumulated_samples" not in state:
            state["accumulated_samples"] = []
        state["accumulated_samples"].append(samples)

        # Decode when at least 0.4s (6400 samples) accumulated or on each step after 0.5s
        all_samples = np.concatenate(state["accumulated_samples"])
        text = state.get("last_text", "")

        if len(all_samples) >= 6400:
            try:
                segments, _ = self.model.transcribe(
                    all_samples,
                    beam_size=1,
                    temperature=0.0,
                    condition_on_previous_text=False,
                    vad_filter=False
                )
                text = " ".join(s.text.strip() for s in segments).strip()
                state["last_text"] = text
            except Exception:
                pass

        return text, state
