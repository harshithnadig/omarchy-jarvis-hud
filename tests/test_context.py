import pytest
from core.context.active_window import WindowContext, _categorize_app, get_active_window
from core.context.privacy import PrivacyEngine
from core.context.profiles import get_style_profile_for_window, PROFILES

def test_categorize_app():
    assert _categorize_app("foot", "terminal") == "terminal"
    assert _categorize_app("kitty", "fish") == "terminal"
    assert _categorize_app("code", "main.py - project") == "code"
    assert _categorize_app("antigravity-ide", "Settings") == "code"
    assert _categorize_app("discord", "general") == "chat"
    assert _categorize_app("google-chrome", "ChatGPT") == "chat"
    assert _categorize_app("google-chrome", "Google Search") == "browser"
    assert _categorize_app("libreoffice-writer", "document.odt") == "document"

def test_privacy_detection():
    privacy = PrivacyEngine()
    
    safe_win = WindowContext(app_class="code", title="main.py", initial_title="VS Code")
    assert privacy.is_sensitive(safe_win) is False
    assert privacy.should_capture_context(safe_win) is True
    assert privacy.should_persist_history(safe_win) is True

    pass_win = WindowContext(app_class="1password", title="1Password Vault", initial_title="1Password")
    assert privacy.is_sensitive(pass_win) is True
    assert privacy.should_capture_context(pass_win) is False
    assert privacy.should_persist_history(pass_win) is False

    auth_win = WindowContext(app_class="polkit-gnome", title="Authentication Required", initial_title="Sudo")
    assert privacy.is_sensitive(auth_win) is True
    assert privacy.should_capture_context(auth_win) is False

def test_private_mode_toggle():
    privacy = PrivacyEngine(private_mode=True)
    safe_win = WindowContext(app_class="code", title="main.py", initial_title="VS Code")
    assert privacy.should_capture_context(safe_win) is False
    assert privacy.should_persist_history(safe_win) is False

def test_style_profiles():
    term_win = WindowContext(app_class="foot", app_category="terminal")
    prof = get_style_profile_for_window(term_win)
    assert prof.name == "terminal"
    assert prof.auto_capitalize is False
    assert prof.paste_shortcut == "ctrl+shift+v"

    code_win = WindowContext(app_class="code", app_category="code")
    prof_code = get_style_profile_for_window(code_win)
    assert prof_code.name == "code"
    assert prof_code.enable_dev_operators is True
