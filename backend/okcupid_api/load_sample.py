"""
Load essential data (tokens, cookies, API config) from sample.json.
Use sample.json for local/dev; keep it out of version control.
"""

import json
from pathlib import Path
from typing import Any, Dict, Optional

# Default path: backend/sample.json when run from backend or project root
_DEFAULT_PATH = Path(__file__).resolve().parent.parent / "sample.json"


def load_sample(path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Load sample.json. Returns dict with keys: auth, api, test_ids.
    Raises FileNotFoundError if file missing.
    """
    p = path or _DEFAULT_PATH
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)


def get_auth(path: Optional[Path] = None) -> Dict[str, Any]:
    """Return auth section: cookies, token, headers."""
    data = load_sample(path)
    return data.get("auth", {})


def get_api(path: Optional[Path] = None) -> Dict[str, Any]:
    """Return api section: base_url, api_host, user_agent."""
    return load_sample(path).get("api", {})


def get_test_ids(path: Optional[Path] = None) -> Dict[str, str]:
    """Return test_ids: profile_user_id, target_user_id, thread_id."""
    return load_sample(path).get("test_ids", {})


def get_swipe_settings(path: Optional[Path] = None) -> Dict[str, Any]:
    """Return swipe settings: direction, max_swipes, delay_seconds."""
    return load_sample(path).get("swipe", {})


def get_graphql_settings(path: Optional[Path] = None) -> Dict[str, Any]:
    """Return graphql settings: swipe_path, discovery_path, etc."""
    return load_sample(path).get("graphql", {})


def get_openai_settings(path: Optional[Path] = None) -> Dict[str, Any]:
    """Return openai settings: api_key, model, temperature, etc."""
    return load_sample(path).get("openai", {})


def get_auto_chat_settings(path: Optional[Path] = None) -> Dict[str, Any]:
    """Return auto_chat settings: funnel, poll_seconds, CTA thresholds, delays."""
    return load_sample(path).get("auto_chat", {})
