import time
import io
import wave
import tempfile
import os
from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from .stt_engine import TranscriptionResult, STTEngine

class StreamingSession(ABC):
    """Abstract interface for true streaming/partial transcription sessions."""
    def __init__(self, engine: STTEngine):
        self.engine = engine
        self.partial_text = ""
        self.total_audio_bytes = 0

    @abstractmethod
    def push_chunk(self, pcm_bytes: bytes) -> Optional[str]:
        """Push a raw PCM audio chunk (16kHz, 16-bit mono) into session. Returns updated partial if changed."""
        pass

    @abstractmethod
    def get_partial(self) -> str:
        """Get the current live partial transcript."""
        pass

    @abstractmethod
    def finalize(self) -> TranscriptionResult:
        """Finalize the session and return the final TranscriptionResult."""
        pass

    @abstractmethod
    def reset(self):
        """Reset the session state for a new utterance."""
        pass


class BufferStreamingSession(StreamingSession):
    """
    Chunk-accumulating streaming session with periodic partial transcription.
    Provides live partial hypotheses for UI display before finalization.
    """
    def __init__(
        self,
        engine: STTEngine,
        sample_rate: int = 16000,
        partial_step_seconds: float = 0.5,
        language: Optional[str] = None,
        hotwords: Optional[str] = None
    ):
        super().__init__(engine=engine)
        self.sample_rate = sample_rate
        self.partial_step_bytes = int(partial_step_seconds * sample_rate * 2)  # 16-bit = 2 bytes per sample
        self.language = language
        self.hotwords = hotwords
        self.buffer = bytearray()
        self.last_transcribed_len = 0
        self.start_time = time.perf_counter()

    def push_chunk(self, pcm_bytes: bytes) -> Optional[str]:
        if not pcm_bytes:
            return None

        self.buffer.extend(pcm_bytes)
        self.total_audio_bytes += len(pcm_bytes)

        # Trigger partial decode when enough new audio has accumulated (e.g. every 0.5s)
        if len(self.buffer) - self.last_transcribed_len >= self.partial_step_bytes:
            self._update_partial()
            return self.partial_text

        return None

    def _update_partial(self):
        if not self.buffer:
            return

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp_path = tmp.name

        try:
            with wave.open(tmp_path, "wb") as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(self.sample_rate)
                wf.writeframes(self.buffer)

            # Fast partial decode (beam_size=1 for lowest latency on partials)
            res = self.engine.transcribe_file(
                tmp_path,
                language=self.language,
                hotwords=self.hotwords,
                beam_size=1
            )
            self.partial_text = res.text
            self.last_transcribed_len = len(self.buffer)
        except Exception:
            pass
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    def get_partial(self) -> str:
        return self.partial_text

    def finalize(self) -> TranscriptionResult:
        if not self.buffer:
            return TranscriptionResult(text="", language=self.language or "en")

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp_path = tmp.name

        try:
            with wave.open(tmp_path, "wb") as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(self.sample_rate)
                wf.writeframes(self.buffer)

            # Full quality decode for final result
            res = self.engine.transcribe_file(
                tmp_path,
                language=self.language,
                hotwords=self.hotwords,
                beam_size=5
            )
            self.partial_text = res.text
            return res
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    def reset(self):
        self.buffer.clear()
        self.partial_text = ""
        self.total_audio_bytes = 0
        self.last_transcribed_len = 0
        self.start_time = time.perf_counter()
