import numpy as np
from faster_whisper.vad import get_vad_model

class SileroVAD:
    """
    Silero VAD wrapper for fast, zero-dependency voice activity detection.
    """
    def __init__(self, threshold: float = 0.35):
        self.threshold = threshold
        self._model = get_vad_model()

    def is_speech(self, chunk_float32: np.ndarray) -> bool:
        """Calculate speech probability for a single audio frame (512 samples @ 16kHz)."""
        prob = float(self._model(chunk_float32)[0])
        return prob > self.threshold

    def get_speech_probability(self, chunk_float32: np.ndarray) -> float:
        return float(self._model(chunk_float32)[0])
