import shutil
import subprocess
from typing import Optional

class AntigravityConnector:
    """
    Interfaces with the local Antigravity CLI (agy) for desktop AI reasoning and system execution.
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
            "Execute the user request and provide a concise, spoken-friendly answer (1-3 sentences max):\n\n"
            f"{prompt}"
        )

        try:
            res = subprocess.run(
                ["agy", "--dangerously-skip-permissions", "-p", agent_prompt],
                capture_output=True,
                text=True,
                timeout=timeout_s
            )
            output = res.stdout.strip()
            if output:
                return output
            return "Task executed successfully."
        except subprocess.TimeoutExpired:
            return "Antigravity agent query timed out."
        except Exception as e:
            return f"Failed to execute Antigravity task: {e}"
