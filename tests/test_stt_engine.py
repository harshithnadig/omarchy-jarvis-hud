import pytest
from core.stt_engine import (
    STTEngine,
    TranscriptionResult,
    EngineUnavailableError,
    InferenceError,
)
from core.nemotron_engine import NemotronEngine
from core.whisper_engine import WhisperEngine

def test_transcription_result_defaults():
    res = TranscriptionResult(text="Hello world")
    assert res.text == "Hello world"
    assert res.confidence is None  # Must not default to fake 1.0 or 0.95
    assert res.latency_ms == 0.0
    assert res.language == "en"

def test_nemotron_unavailable_behavior():
    nem = NemotronEngine()
    if not nem.is_available():
        with pytest.raises(EngineUnavailableError):
            nem.load_model()
        with pytest.raises((EngineUnavailableError, InferenceError)):
            nem.transcribe_file("/tmp/non_existent.wav")

def test_whisper_missing_file():
    whisper = WhisperEngine(model_id="large-v3-turbo")
    with pytest.raises(InferenceError):
        whisper.transcribe_file("/tmp/definitely_non_existent_audio_file.wav")
