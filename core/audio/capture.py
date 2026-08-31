import sounddevice as sd
import numpy as np
from typing import Generator, Optional, Callable
from .endpoint import EndpointDetector

class AudioCapture:
    """
    Microphone capture stream with integrated Silero VAD and endpointing.
    """
    def __init__(
        self,
        sample_rate: int = 16000,
        chunk_size: int = 512,
        silence_timeout_s: float = 0.55
    ):
        self.sample_rate = sample_rate
        self.chunk_size = chunk_size
        self.silence_timeout_s = silence_timeout_s

    def record_utterance(
        self,
        max_duration_s: float = 15.0,
        on_chunk: Optional[Callable[[bytes], None]] = None
    ) -> bytes:
        """
        Record until silence endpoint is detected or max duration is reached.
        """
        detector = EndpointDetector(
            sample_rate=self.sample_rate,
            chunk_size=self.chunk_size,
            silence_timeout_s=self.silence_timeout_s
        )

        audio_frames = []
        max_frames = int(max_duration_s * self.sample_rate / self.chunk_size)

        with sd.InputStream(samplerate=self.sample_rate, channels=1, blocksize=self.chunk_size, dtype='float32') as stream:
            for _ in range(max_frames):
                data, _ = stream.read(self.chunk_size)
                chunk = data[:, 0]
                raw_pcm = (chunk * 32767).astype(np.int16).tobytes()

                if on_chunk:
                    on_chunk(raw_pcm)

                is_endpoint = detector.process_frame(chunk)
                if detector.speech_started:
                    audio_frames.append(raw_pcm)

                if is_endpoint:
                    break

        return b"".join(audio_frames)
