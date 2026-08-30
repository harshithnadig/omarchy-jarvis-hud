from abc import ABC, abstractmethod

class TextInjectionError(Exception):
    """Raised when text injection into active window fails."""
    pass

class TextInjector(ABC):
    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def is_available(self) -> bool:
        """Check if required CLI binaries / system dependencies exist."""
        pass

    @abstractmethod
    def inject(self, text: str) -> bool:
        """Inject text into current active window / cursor."""
        pass
