"""
Print your OkCupid profile/settings info to the console.

Usage (from backend/):
    python -m examples.show_profile_settings
"""

import os
import sys
from pprint import pprint
from typing import Any, Dict, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover
    load_dotenv = lambda: None  # type: ignore[assignment]

from okcupid_api import OkCupidClient
from okcupid_api import profile


def get_profile_summary(client: OkCupidClient) -> Dict[str, Any]:
    """
    Shared helper used by both this example script and the API server.

    Returns a compact dict containing the settings/me object and bio info
    (including text and avatar URL) for the currently-authenticated user.
    """
    me = profile.get_my_profile_settings(client)

    # Try to get bio using WebProfileSelf; fall back gracefully if user id missing.
    user_id: Optional[str] = None
    if isinstance(me, dict):
        user_id = me.get("id")

    bio_payload: Optional[Dict[str, Any]]
    error: Optional[str] = None
    try:
        bio_payload = profile.get_my_bio(client, user_id=user_id)
    except Exception as exc:  # noqa: BLE001
        bio_payload = None
        error = str(exc)

    bio_text: Optional[str] = None
    avatar_url: Optional[str] = None
    if isinstance(bio_payload, dict):
        bio_text = bio_payload.get("text")
        avatar_url = bio_payload.get("avatar_url")

    return {
        "settings": me,
        "bio": {
            "raw": bio_payload,
            "text": bio_text,
            "avatar_url": avatar_url,
            "error": error,
        },
    }


def main() -> None:
    load_dotenv()

    try:
        client = OkCupidClient.from_sample()
    except FileNotFoundError:
        base = os.getenv("OKCUPID_API_BASE", "https://www.okcupid.com")
        cookies = {}
        for k, v in os.environ.items():
            if k.startswith("OKCUPID_COOKIE_"):
                cookies[k.replace("OKCUPID_COOKIE_", "", 1)] = v
        client = OkCupidClient(base_url=base, cookies=cookies or None)

    summary = get_profile_summary(client)
    print("=== Me (WebSettingsPage) ===")
    pprint(summary.get("settings"))
    print("=== Bio text ===")
    pprint(summary.get("bio", {}).get("text"))
    print("=== Avatar URL ===")
    pprint(summary.get("bio", {}).get("avatar_url"))
    if summary.get("bio", {}).get("error"):
        print("=== Bio error ===")
        pprint(summary["bio"]["error"])


if __name__ == "__main__":
    main()

