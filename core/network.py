"""Small helpers for bounded reads from local and remote HTTP responses."""


class ResponseTooLargeError(ValueError):
    """Raised when an HTTP response exceeds the caller's byte budget."""


def read_response_limited(response, max_bytes):
    """Read at most ``max_bytes`` and reject oversized or invalid lengths.

    A response may omit Content-Length, so the body is still streamed in
    bounded chunks and aborted as soon as the cap is crossed. This keeps
    attacker-controlled responses from being fully buffered in memory.
    """
    if max_bytes <= 0:
        raise ValueError("max_bytes must be positive")

    headers = getattr(response, "headers", None)
    lengths = []
    if headers is not None:
        get_all = getattr(headers, "get_all", None)
        if callable(get_all):
            lengths = get_all("Content-Length") or []
        elif hasattr(headers, "get"):
            value = headers.get("Content-Length")
            lengths = [] if value is None else [value]

    if lengths:
        normalized = [str(value).strip() for value in lengths]
        if len(set(normalized)) != 1:
            raise ResponseTooLargeError("conflicting Content-Length headers")
        try:
            content_length = int(normalized[0])
        except (TypeError, ValueError) as error:
            raise ResponseTooLargeError("invalid Content-Length header") from error
        if content_length < 0 or content_length > max_bytes:
            raise ResponseTooLargeError(
                f"Content-Length {content_length} exceeds {max_bytes} bytes"
            )

    chunks = []
    total = 0
    while True:
        chunk = response.read(min(64 * 1024, max_bytes - total + 1))
        if not chunk:
            break
        total += len(chunk)
        if total > max_bytes:
            raise ResponseTooLargeError(
                f"response exceeds the {max_bytes}-byte limit"
            )
        chunks.append(chunk)
    return b"".join(chunks)
