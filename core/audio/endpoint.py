import numpy as np
from typing import Optional
from .vad import SileroVAD

class EndpointDetector:
    """
    Tracks speech state, onset, and silence endpoints.
    """
    def __init__(
        self,
        sample_rate: int = 16000,
        chunk_size: int = 512,
        silence_timeout_s: float = 0.55,
        min_speech_frames: int = 6,
        vad_threshold: float = 0.35
    ):
        self.sample_rate = sample_rate
        self.chunk_size = chunk_size
        self.silence_limit_frames = int(silence_timeout_s * sample_rate / chunk_size)
        self.min_speech_frames = min_speech_frames
        self.vad = SileroVAD(threshold=vad_threshold)

        self.speech_started = False
        self.speech_frames = 0
        self.silence_frames = 0

    def process_frame(self, chunk: np.ndarray) -> bool:
        """
        Process an audio frame. Returns True if utterance endpoint has been reached.
        """
        if self.vad.is_speech(chunk):
            self.speech_started = True
            self.speech_frames += 1
            self.silence_frames = 0
        else:
            if self.speech_started:
                self.silence_frames += 1
                if self.silence_frames > self.silence_limit_frames and self.speech_frames >= self.min_speech_frames:
                    return True  # Endpoint reached

        return False

    def reset(self):
        self.speech_started = False
        self.speech_frames = 0
        self.silence_frames = 0
