import os
import json
import pytest
from benchmarks.dataset import BenchmarkSample, load_manifest, save_manifest
from benchmarks.runner import BenchmarkRunner

def test_benchmark_sample_serialization():
    sample = BenchmarkSample(
        id="test_01",
        audio_path="/tmp/test.wav",
        reference_text="hello world",
        category="dev_terms",
        language="en",
        duration_s=2.5,
        tags=["unit_test"]
    )
    d = sample.to_dict()
    assert d["id"] == "test_01"
    assert d["category"] == "dev_terms"
    
    restored = BenchmarkSample.from_dict(d)
    assert restored.id == sample.id
    assert restored.reference_text == sample.reference_text

def test_manifest_save_and_load(tmp_path):
    manifest_file = str(tmp_path / "manifest.json")
    samples = [
        BenchmarkSample(id="s1", audio_path="s1.wav", reference_text="ref 1"),
        BenchmarkSample(id="s2", audio_path="s2.wav", reference_text="ref 2"),
    ]
    save_manifest(samples, manifest_file)
    assert os.path.exists(manifest_file)

    loaded = load_manifest(manifest_file)
    assert len(loaded) == 2
    assert loaded[0].id == "s1"
    assert loaded[1].id == "s2"
    assert loaded[0].audio_path == str(tmp_path / "s1.wav")
