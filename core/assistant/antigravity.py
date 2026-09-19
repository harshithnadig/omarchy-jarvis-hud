import os
import selectors
import shutil
import signal
import subprocess
import time


MAX_AGENT_OUTPUT_BYTES = 64 * 1024
OUTPUT_READ_CHUNK_BYTES = 4096


def _terminate_process_group(process):
    """Terminate the agent and any descendants created in its process group."""
    if process.poll() is not None:
        return
    try:
        os.killpg(process.pid, signal.SIGTERM)
    except (ProcessLookupError, PermissionError, OSError):
        process.terminate()
    try:
        process.wait(timeout=1)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except (ProcessLookupError, PermissionError, OSError):
            process.kill()
        process.wait(timeout=1)


def _collect_output(process, timeout_s):
    """Drain both pipes continuously while retaining only bounded prefixes."""
    selector = selectors.DefaultSelector()
    buffers = {"stdout": bytearray(), "stderr": bytearray()}
    truncated = {"stdout": False, "stderr": False}
    for stream, name in ((process.stdout, "stdout"), (process.stderr, "stderr")):
        if stream is None:
            continue
        os.set_blocking(stream.fileno(), False)
        selector.register(stream, selectors.EVENT_READ, name)

    timed_out = False
    deadline = time.monotonic() + max(0.0, float(timeout_s))
    try:
        while selector.get_map():
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                timed_out = process.poll() is None
                if timed_out:
                    _terminate_process_group(process)
                break

            events = selector.select(min(remaining, 0.25))
            for key, _ in events:
                try:
                    data = os.read(key.fileobj.fileno(), OUTPUT_READ_CHUNK_BYTES)
                except BlockingIOError:
                    continue
                if not data:
                    selector.unregister(key.fileobj)
                    continue

                name = key.data
                available = MAX_AGENT_OUTPUT_BYTES - len(buffers[name])
                if available > 0:
                    buffers[name].extend(data[:available])
                if len(data) > max(0, available):
                    truncated[name] = True

        if process.poll() is None:
            _terminate_process_group(process)
        else:
            process.wait(timeout=1)
    finally:
        selector.close()

    return (
        bytes(buffers["stdout"]),
        bytes(buffers["stderr"]),
        timed_out,
        truncated["stdout"],
        truncated["stderr"],
    )

class AntigravityConnector:
    """
    Interfaces with the local Antigravity CLI (agy) for desktop AI reasoning.

    The voice confirmation is only a routing gate. The CLI is intentionally
    invoked without a permission-bypass option so its own local permission
    prompt remains the independent authorization boundary for tool actions.
    """
    @classmethod
    def is_available(cls) -> bool:
        return shutil.which("agy") is not None

    @classmethod
    def query(cls, prompt: str, timeout_s: int = 120) -> str:
        if not cls.is_available():
            return "Antigravity CLI (agy) is not installed or not in PATH."

        agent_prompt = (
            "You are JARVIS, an AI assistant on Omarchy Linux. "
            "Provide a concise, conversational answer (1-3 sentences max). "
            "Do NOT execute any unconfirmed system modifications without explicit user approval:\n\n"
            f"{prompt}"
        )

        process = None
        try:
            # start_new_session gives the process a private group so timeout
            # cleanup also terminates/reaps descendants, not just agy itself.
            process = subprocess.Popen(
                ["agy", "-p", agent_prompt],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                start_new_session=True,
            )
            stdout, stderr, timed_out, stdout_truncated, stderr_truncated = _collect_output(
                process, timeout_s
            )
            if timed_out:
                return "Antigravity agent query timed out."

            output = stdout.decode("utf-8", errors="replace").strip()
            if stdout_truncated:
                output += "\n[Antigravity output truncated.]"
            if output:
                return output
            if process.returncode != 0:
                error = stderr.decode("utf-8", errors="replace").strip()
                if stderr_truncated:
                    error += " [error output truncated]"
                if error:
                    return f"Antigravity failed: {error[:240]}"
                return "Antigravity declined the request."
            return "Antigravity returned no response."
        except Exception as error:
            if process is not None:
                _terminate_process_group(process)
            return f"Failed to execute Antigravity task: {error}"
