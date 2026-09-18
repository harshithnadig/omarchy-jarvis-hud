from dataclasses import dataclass
import re
from typing import Optional
from .actions import LocalActionExecutor, PermissionClass
from .antigravity import AntigravityConnector

@dataclass
class AssistantResponse:
    spoken_text: str
    permission_class: PermissionClass
    executed_by: str  # "fast_path", "confirmation_required", or "antigravity"
    pending_query: Optional[str] = None

class AssistantRouter:
    """
    Routes user voice commands in Mode B (Assistant Mode).
    1. Evaluates fast-path commands (< 50ms).
    2. Requires a separate explicit confirmation before the Antigravity CLI
       can receive a complex query.
    """

    _CONFIRMATION_PHRASES = {
        "confirm",
        "confirm it",
        "confirm request",
        "i confirm",
        "i confirm it",
        "yes confirm",
        "yes i confirm",
        "approve",
        "approve request",
    }

    @classmethod
    def process_query(cls, query: str) -> AssistantResponse:
        if not query or not query.strip():
            return AssistantResponse(
                spoken_text="I did not hear a command.",
                permission_class=PermissionClass.SAFE,
                executed_by="fast_path"
            )

        # 1. Check fast path
        fast_result = LocalActionExecutor.match_and_execute(query)
        if fast_result is not None:
            text, perm = fast_result
            return AssistantResponse(
                spoken_text=text,
                permission_class=perm,
                executed_by="fast_path"
            )

        # 2. Do not forward arbitrary speech/transcription to an agent. The
        # caller must collect a second, explicit confirmation and then call
        # confirm_query(). Keeping the pending text in the response makes the
        # boundary visible and prevents a boolean flag from being accidentally
        # threaded through a future caller.
        return AssistantResponse(
            spoken_text=(
                "That request may change your system. Say 'confirm' in a "
                "separate response if you want me to send it to Antigravity."
            ),
            permission_class=PermissionClass.SENSITIVE,
            executed_by="confirmation_required",
            pending_query=query.strip(),
        )

    @classmethod
    def confirm_query(cls, pending_query: str, confirmation: str) -> AssistantResponse:
        """Forward a pending query only after an exact confirmation phrase."""
        query = (pending_query or "").strip()
        normalized = re.sub(r"[^a-z0-9\s]", " ", (confirmation or "").lower())
        normalized = re.sub(r"\s+", " ", normalized).strip()

        if not query or normalized not in cls._CONFIRMATION_PHRASES:
            return AssistantResponse(
                spoken_text="Cancelled. No agent action was sent.",
                permission_class=PermissionClass.SAFE,
                executed_by="confirmation_denied",
            )

        agent_reply = AntigravityConnector.query(query)
        return AssistantResponse(
            spoken_text=agent_reply,
            permission_class=PermissionClass.SENSITIVE,
            executed_by="antigravity",
        )
