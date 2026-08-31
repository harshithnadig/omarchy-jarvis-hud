import pytest
from core.router import EngineRouter
from core.stt_engine import EngineUnavailableError

def test_router_default():
    router = EngineRouter(default_engine="turbo")
    assert router.active_engine_key == "turbo"
    assert router.get_engine().name == "whisper-large-v3-turbo"

def test_router_switch_valid():
    router = EngineRouter()
    router.set_default_engine("large-v3")
    assert router.active_engine_key == "large-v3"
    assert router.get_engine().name == "whisper-large-v3"

def test_router_switch_invalid():
    router = EngineRouter()
    with pytest.raises(EngineUnavailableError):
        router.set_default_engine("non_existent_engine")

def test_router_get_unknown():
    router = EngineRouter()
    with pytest.raises(EngineUnavailableError):
        router.get_engine("invalid_key", allow_fallback=False)

def test_router_get_unknown_fallback():
    router = EngineRouter(default_engine="turbo")
    eng = router.get_engine("invalid_key", allow_fallback=True)
    assert eng.name == "whisper-large-v3-turbo"

def test_router_list_engines():
    router = EngineRouter()
    engines = router.list_engines()
    keys = [e["key"] for e in engines]
    assert "turbo" in keys
    assert "large-v3" in keys
    assert "nemotron" in keys
    for e in engines:
        assert "is_available" in e
        assert "is_loaded" in e

def test_route_engine_policy():
    from unittest.mock import patch
    router = EngineRouter(default_engine="turbo")

    # When large-v3 is available
    with patch.object(router._engines["large-v3"], "is_available", return_value=True):
        assert router.route_engine(audio_duration_s=3.0, language="en") == "turbo"
        assert router.route_engine(require_max_accuracy=True) == "large-v3"
        assert router.route_engine(audio_duration_s=25.0, language="es") == "large-v3"

    # When large-v3 is unavailable (graceful fallback)
    with patch.object(router._engines["large-v3"], "is_available", return_value=False):
        assert router.route_engine(require_max_accuracy=True) == "turbo"
        assert router.route_engine(audio_duration_s=25.0, language="es") == "turbo"

