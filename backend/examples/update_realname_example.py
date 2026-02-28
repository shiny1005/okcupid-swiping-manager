"""
Example: update your OkCupid real name using WebUpdateRealname.

Usage (from backend/):
    python -m examples.update_realname_example
"""

import os
import sys
from typing import Dict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover
    load_dotenv = lambda: None  # type: ignore[assignment]

from okcupid_api import OkCupidClient
from okcupid_api import profile
from okcupid_api.load_sample import get_profile_settings


def update_realname_for_client(client: OkCupidClient, new_realname: str) -> Dict:
    """
    Shared helper used by both this example script and the API server to
    update the current user's real name.
    """
    return profile.update_realname(client, new_realname)


def main() -> None:
    load_dotenv()

    try:
        client = OkCupidClient.from_sample()
        profile_cfg = get_profile_settings()
    except FileNotFoundError:
        base = os.getenv("OKCUPID_API_BASE", "https://www.okcupid.com")
        cookies = {}
        for k, v in os.environ.items():
            if k.startswith("OKCUPID_COOKIE_"):
                cookies[k.replace("OKCUPID_COOKIE_", "", 1)] = v
        client = OkCupidClient(base_url=base, cookies=cookies or None)
        profile_cfg = {}

    new_realname = (
        os.getenv("NEW_REALNAME")
        or str(profile_cfg.get("realname") or "").strip()
        or "Esthe r"
    )

    result = update_realname_for_client(client, new_realname)
    print("=== WebUpdateRealname result ===")
    print(result)


if __name__ == "__main__":
    main()

