import os
import json
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional

@dataclass
class BenchmarkSample:
    id: str
    audio_path: str
    reference_text: str = ""
    category: str = "general"
    language: str = "en"
    duration_s: float = 0.0
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BenchmarkSample":
        return cls(
            id=data["id"],
            audio_path=data["audio_path"],
            reference_text=data.get("reference_text", ""),
            category=data.get("category", "general"),
            language=data.get("language", "en"),
            duration_s=data.get("duration_s", 0.0),
            tags=data.get("tags", []),
        )

def load_manifest(manifest_path: str) -> List[BenchmarkSample]:
    """Load benchmark samples from a JSON or JSONL manifest."""
    if not os.path.exists(manifest_path):
        raise FileNotFoundError(f"Manifest not found: {manifest_path}")

    samples = []
    base_dir = os.path.dirname(os.path.abspath(manifest_path))

    with open(manifest_path, "r", encoding="utf-8") as f:
        content = f.read().strip()
        if content.startswith("["):
            data = json.loads(content)
            for item in data:
                # Resolve relative audio paths against manifest directory
                if not os.path.isabs(item["audio_path"]):
                    item["audio_path"] = os.path.join(base_dir, item["audio_path"])
                samples.append(BenchmarkSample.from_dict(item))
        else:
            # JSONL format
            for line in content.splitlines():
                if line.strip():
                    item = json.loads(line)
                    if not os.path.isabs(item["audio_path"]):
                        item["audio_path"] = os.path.join(base_dir, item["audio_path"])
                    samples.append(BenchmarkSample.from_dict(item))
    return samples

def save_manifest(samples: List[BenchmarkSample], manifest_path: str):
    """Save benchmark samples list to JSON manifest."""
    os.makedirs(os.path.dirname(os.path.abspath(manifest_path)), exist_ok=True)
    data = [s.to_dict() for s in samples]
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
