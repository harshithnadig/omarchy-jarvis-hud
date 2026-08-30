from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List

@dataclass
class TranscriptionResult:
    text: str
    language: str = "en"
    confidence: float = 1.0
    latency_ms: float = 0.0
    audio_duration_s: float = 0.0
    rtf: float = 0.0  # Real-Time Factor (processing_time / audio_duration)
    engine_name: str = "unknown"
    metadata: Dict[str, Any] = field(default_factory=dict)

class STTEngine(ABC):
    def __init__(self, name: str):
        self.name = name
        self.is_loaded = False

    @abstractmethod
    def load_model(self, device: str = "cuda", compute_type: str = "float16"):
        """Load model weights into memory/VRAM."""
        pass

    @abstractmethod
    def transcribe_file(
        self,
        audio_path: str,
        language: Optional[str] = None,
        hotwords: Optional[str] = None,
        **kwargs
    ) -> TranscriptionResult:
        """Transcribe an audio file from disk."""
        pass

    def unload_model(self):
        """Free VRAM/memory if needed."""
        self.is_loaded = False
