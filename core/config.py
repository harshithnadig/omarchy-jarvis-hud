import os
import tomllib
from typing import Dict, Any

USER_CONFIG_PATH = os.path.expanduser("~/.config/jarvis-voice/config.toml")
REPO_CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config.toml")

def load_config() -> Dict[str, Any]:
    """Load unified configuration with fallback priority: User XDG config -> Repo config -> Defaults."""
    config_file = USER_CONFIG_PATH if os.path.exists(USER_CONFIG_PATH) else REPO_CONFIG_PATH

    defaults = {
        "dictation": {
            "default_engine": "turbo",
            "preferred_injector": "auto",
            "enable_polish": True,
            "enable_backtracking": True,
            "dev_mode": True,
            "hotkey": "SUPER+SPACE"
        },
        "assistant": {
            "hotkey": "SUPER+J",
            "voice": "en-US-ChristopherNeural",
            "enable_tts": True,
            "agy_timeout_s": 120
        },
        "privacy": {
            "local_only": True,
            "save_audio": False,
            "save_transcripts": False,
            "private_mode": False
        },
        "server": {
            "host": "127.0.0.1",
            "port": 8765
        }
    }

    if os.path.exists(config_file):
        try:
            with open(config_file, "rb") as f:
                parsed = tomllib.load(f)
                for section, values in parsed.items():
                    if section in defaults and isinstance(values, dict):
                        defaults[section].update(values)
                    else:
                        defaults[section] = values
        except Exception as e:
            print(f"⚠️ [Config] Failed to parse {config_file} ({e}), using defaults.")

    return defaults
