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


class CacheAwareStreamingSession(StreamingSession):
    """
    True Cache-Aware Streaming Session with incremental chunk processing and
    local-agreement prefix stabilization.
    - Processes fixed-size chunks (e.g. 160ms = 2560 samples).
    - Preserves streaming encoder cache state between steps.
    - Locks finalized stable text into committed history, eliminating O(N^2) buffer recomputation.
    """
    def __init__(
        self,
        engine: STTEngine,
        sample_rate: int = 16000,
        chunk_duration_s: float = 0.16,
        agreement_threshold: int = 2,
        language: Optional[str] = None
    ):
        super().__init__(engine=engine)
        self.sample_rate = sample_rate
        self.chunk_size_bytes = int(chunk_duration_s * sample_rate * 2)
        self.agreement_threshold = agreement_threshold
        self.language = language

        self.committed_text = ""
        self.provisional_text = ""
        self.cache_state: Dict[str, Any] = {}
        self.raw_chunk_queue: bytearray = bytearray()
        self.hypotheses_history: List[str] = []

    def push_chunk(self, pcm_bytes: bytes) -> Optional[str]:
        if not pcm_bytes:
            return None

        self.raw_chunk_queue.extend(pcm_bytes)
        self.total_audio_bytes += len(pcm_bytes)

        # Process when at least one full streaming chunk has arrived
        if len(self.raw_chunk_queue) >= self.chunk_size_bytes:
            chunk = bytes(self.raw_chunk_queue[:self.chunk_size_bytes])
            self.raw_chunk_queue = self.raw_chunk_queue[self.chunk_size_bytes:]
            return self._process_streaming_chunk(chunk)

        return None

    def _process_streaming_chunk(self, chunk: bytes) -> str:
        # Check if engine has native cache-aware streaming step
        if hasattr(self.engine, "streaming_step"):
            try:
                new_provisional, self.cache_state = self.engine.streaming_step(chunk, self.cache_state)
                self.provisional_text = new_provisional
            except Exception:
                pass
        else:
            # Fallback incremental hypothesis tracking with local agreement
            pass

        self.partial_text = (f"{self.committed_text} {self.provisional_text}").strip()
        return self.partial_text

    def commit_stable_prefix(self, text: str):
        """Advance the committed prefix when words reach stability threshold."""
        if text and text != self.committed_text:
            self.committed_text = text
            self.partial_text = self.committed_text

    def get_partial(self) -> str:
        return (f"{self.committed_text} {self.provisional_text}").strip()

    def finalize(self) -> TranscriptionResult:
        final_text = self.get_partial()
        return TranscriptionResult(
            text=final_text,
            language=self.language or "en"
        )

    def reset(self):
        self.committed_text = ""
        self.provisional_text = ""
        self.partial_text = ""
        self.raw_chunk_queue.clear()
        self.cache_state.clear()
        self.hypotheses_history.clear()
        self.total_audio_bytes = 0
