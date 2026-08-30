from abc import ABC, abstractmethod
from typing import Dict, Any, Generator

class STTEngine(ABC):
    @abstractmethod
    def load_model(self):
        """Load the model into memory."""
        pass

    @abstractmethod
    def transcribe_batch(self, audio_path: str, **kwargs) -> str:
        """Process an entire audio file at once (legacy/fallback mode)."""
        pass

    @abstractmethod
    def transcribe_stream(self, audio_stream, **kwargs) -> Generator[str, None, None]:
        """Process an audio stream yielding tokens/words in real-time."""
        pass
