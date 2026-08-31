import numpy as np
from typing import Optional

class SileroVAD:
    """
    Silero VAD wrapper for fast, zero-dependency voice activity detection.
    Falls back gracefully to RMS energy detection if faster_whisper is not installed.
    """
    def __init__(self, threshold: float = 0.35):
        self.threshold = threshold
        self._model = None
        self._is_silero = False

        try:
            from faster_whisper.vad import get_vad_model
            self._model = get_vad_model()
            self._is_silero = True
        except ImportError:
            self._model = None
            self._is_silero = False

    def get_speech_probability(self, chunk_float32: np.ndarray) -> float:
        """Calculate speech probability for a single audio frame (512 samples @ 16kHz)."""
        if self._is_silero and self._model is not None:
            try:
                return float(self._model(chunk_float32)[0])
            except Exception:
                pass

        # Robust RMS Energy Fallback for lightweight / CI test environments
        if len(chunk_float32) == 0:
            return 0.0
        rms = float(np.sqrt(np.mean(chunk_float32 ** 2)))
        # Map typical microphonic RMS range [0.001, 0.05] into [0.0, 1.0] probability
        prob = min(max((rms - 0.002) / 0.04, 0.0), 1.0)
        return prob

    def is_speech(self, chunk_float32: np.ndarray) -> bool:
        prob = self.get_speech_probability(chunk_float32)
        return prob > self.threshold
