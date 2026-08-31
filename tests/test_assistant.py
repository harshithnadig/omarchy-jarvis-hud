import pytest
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
