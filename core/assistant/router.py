from dataclasses import dataclass
from typing import Optional, Tuple
from .actions import LocalActionExecutor, PermissionClass
from .antigravity import AntigravityConnector

@dataclass
class AssistantResponse:
    spoken_text: str
    permission_class: PermissionClass
    executed_by: str  # "fast_path" or "antigravity"

class AssistantRouter:
    """
    Routes user voice commands in Mode B (Assistant Mode).
    1. Evaluates fast-path commands (< 50ms).
    2. Falls back to Antigravity CLI agent for complex queries.
    """

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

        # 2. Forward to Antigravity agent
        agent_reply = AntigravityConnector.query(query)
        return AssistantResponse(
            spoken_text=agent_reply,
            permission_class=PermissionClass.SENSITIVE,
            executed_by="antigravity"
        )
