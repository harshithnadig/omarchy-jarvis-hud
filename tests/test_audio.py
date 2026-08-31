import pytest
import numpy as np
from core.audio.vad import SileroVAD
from core.audio.endpoint import EndpointDetector

def test_silero_vad_silence():
    vad = SileroVAD()
    # Zero audio frame
    silence = np.zeros(512, dtype=np.float32)
    prob = vad.get_speech_probability(silence)
    assert prob < 0.20
    assert vad.is_speech(silence) is False

def test_endpoint_detector_lifecycle():
    detector = EndpointDetector(silence_timeout_s=0.1, min_speech_frames=2)
    silence = np.zeros(512, dtype=np.float32)

    # Initial state
    assert detector.speech_started is False
    assert detector.process_frame(silence) is False

    detector.reset()
    assert detector.speech_started is False
