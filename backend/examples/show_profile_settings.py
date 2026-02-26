"""
Print your OkCupid profile/settings info to the console.

Usage (from backend/):
    python -m examples.show_profile_settings
"""

import os
import sys
from pprint import pprint

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover
    load_dotenv = lambda: None  # type: ignore[assignment]

from okcupid_api import OkCupidClient
from okcupid_api import profile


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

    me = profile.get_my_profile_settings(client)

    print("=== Me (WebSettingsPage) ===")
    pprint(me)


if __name__ == "__main__":
    main()

