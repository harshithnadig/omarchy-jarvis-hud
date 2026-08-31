import pytest
from core.router import EngineRouter
from core.streaming import BufferStreamingSession

def test_streaming_session_lifecycle():
    router = EngineRouter(default_engine="turbo")
    session = router.start_streaming_session()

    assert isinstance(session, BufferStreamingSession)
    assert session.get_partial() == ""
    assert session.total_audio_bytes == 0

    # Push empty chunk
    session.push_chunk(b"")
    assert session.get_partial() == ""

    # Push dummy PCM bytes (not enough to trigger partial)
    session.push_chunk(b"\x00\x00" * 100)
    assert session.total_audio_bytes == 200

    # Reset
    session.reset()
    assert session.total_audio_bytes == 0
    assert session.get_partial() == ""

def test_cache_aware_streaming_session():
    from core.streaming import CacheAwareStreamingSession
    router = EngineRouter(default_engine="turbo")
    engine = router.get_engine("turbo")
    session = CacheAwareStreamingSession(engine=engine, chunk_duration_s=0.16)

    assert session.get_partial() == ""
    assert session.total_audio_bytes == 0

    # Push small sub-chunk (not full chunk size)
    session.push_chunk(b"\x00\x00" * 100)
    assert session.total_audio_bytes == 200

    # Push enough to complete chunk
    session.push_chunk(b"\x00\x00" * 3000)
    assert session.total_audio_bytes == 6200

    session.commit_stable_prefix("hello world")
    assert "hello world" in session.get_partial()

    res = session.finalize()
    assert res.text == "hello world"
