import pytest
from unittest.mock import patch
from core.assistant.actions import LocalActionExecutor, PermissionClass
from core.assistant.router import AssistantRouter

def test_local_action_greetings():
    res = LocalActionExecutor.match_and_execute("Hey Jarvis, hello")
    assert res is not None
    text, perm = res
    assert "Hello" in text or "JARVIS" in text
    assert perm == PermissionClass.SAFE

def test_local_action_time():
    res = LocalActionExecutor.match_and_execute("What time is it?")
    assert res is not None
    text, perm = res
    assert "currently" in text
    assert perm == PermissionClass.SAFE

def test_local_action_battery():
    res = LocalActionExecutor.match_and_execute("What is my battery level?")
    # Battery can be None if battery file doesn't exist on host, but if matched returns SAFE
    if res is not None:
        text, perm = res
        assert "Battery" in text
        assert perm == PermissionClass.SAFE

def test_assistant_router_fast_path():
    resp = AssistantRouter.process_query("What time is it?")
    assert resp.executed_by == "fast_path"
    assert resp.permission_class == PermissionClass.SAFE


def test_agent_request_requires_separate_confirmation():
    with patch("core.assistant.router.AntigravityConnector.query") as query:
        pending = AssistantRouter.process_query("delete the old build artifacts")

        assert pending.executed_by == "confirmation_required"
        assert pending.permission_class == PermissionClass.SENSITIVE
        assert pending.pending_query == "delete the old build artifacts"
        query.assert_not_called()

        approved = AssistantRouter.confirm_query(pending.pending_query, "I confirm")

    assert approved.executed_by == "antigravity"
    query.assert_called_once_with("delete the old build artifacts")


def test_agent_request_rejects_ambiguous_confirmation():
    with patch("core.assistant.router.AntigravityConnector.query") as query:
        pending = AssistantRouter.process_query("change my firewall rules")
        denied = AssistantRouter.confirm_query(pending.pending_query, "yes")

    assert denied.executed_by == "confirmation_denied"
    assert denied.permission_class == PermissionClass.SAFE
    query.assert_not_called()


def test_voice_entrypoints_cannot_bypass_confirmation_gate():
    for filename in ("jarvis-ptt", "jarvis_daemon.py"):
        with open(filename, encoding="utf-8") as handle:
            source = handle.read()
        assert "dangerously-skip-permissions" not in source
        assert "AssistantRouter.process_query" in source
        assert "AssistantRouter.confirm_query" in source


def test_antigravity_keeps_independent_cli_permission_boundary():
    with open("core/assistant/antigravity.py", encoding="utf-8") as handle:
        source = handle.read()
    assert "dangerously-skip-permissions" not in source
    assert "start_new_session=True" in source
    assert "MAX_AGENT_OUTPUT_BYTES" in source


def test_push_to_talk_uses_a_private_non_following_lock():
    with open("jarvis-ptt", encoding="utf-8") as handle:
        source = handle.read()
    assert "/tmp/jarvis_ptt.pid" not in source
    assert "O_NOFOLLOW" in source
    assert "LOCK_NB" in source
