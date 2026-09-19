import pytest

from core.network import ResponseTooLargeError, read_response_limited


class FakeHeaders(dict):
    def get_all(self, name):
        value = self.get(name)
        return [] if value is None else [value]


class FakeResponse:
    def __init__(self, chunks, content_length=None):
        self.chunks = list(chunks)
        self.headers = FakeHeaders()
        if content_length is not None:
            self.headers["Content-Length"] = str(content_length)

    def read(self, size=-1):
        if not self.chunks:
            return b""
        chunk = self.chunks.pop(0)
        if size >= 0 and len(chunk) > size:
            self.chunks.insert(0, chunk[size:])
            return chunk[:size]
        return chunk


def test_bounded_reader_accepts_exact_limit():
    response = FakeResponse([b"abc", b"def"], content_length=6)
    assert read_response_limited(response, 6) == b"abcdef"


def test_bounded_reader_rejects_oversized_content_length():
    response = FakeResponse([b"not read"], content_length=7)
    with pytest.raises(ResponseTooLargeError):
        read_response_limited(response, 6)
    assert response.chunks == [b"not read"]


def test_bounded_reader_aborts_stream_without_content_length():
    response = FakeResponse([b"1234", b"5678"])
    with pytest.raises(ResponseTooLargeError):
        read_response_limited(response, 6)
