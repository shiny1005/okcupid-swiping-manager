"""
Example usage of OkCupid API client (after endpoints are filled from reverse engineering).
Run from backend: python -m examples.usage
"""

import os
import sys

# Allow importing okcupid_api from repo root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = lambda: None

from okcupid_api import OkCupidClient
from okcupid_api import profile, bio, swipe, ai_chat


def main() -> None:
    load_dotenv()
    # Prefer sample.json (copy sample.json.example → sample.json and fill in)
    try:
        client = OkCupidClient.from_sample()
    except FileNotFoundError:
        base = os.getenv("OKCUPID_API_BASE", "https://www.okcupid.com")
        cookies = {}
        for k, v in os.environ.items():
            if k.startswith("OKCUPID_COOKIE_"):
                cookies[k.replace("OKCUPID_COOKIE_", "", 1)] = v
        client = OkCupidClient(base_url=base, cookies=cookies or None)

    # Stub calls – will 404 until real endpoints are set in config
    print("Profile (single):", "call get_profile(client, 'USER_ID')")
    print("Profile (bulk):", "call get_profiles_bulk(client, ['id1', 'id2'])")
    print("Bio (single):", "call edit_bio(client, 'New bio')")
    print("Bio (bulk):", "call edit_bio_bulk(client, [{'user_id':'x','bio':'...'}])")
    print("Swipe (single):", "call swipe(client, 'TARGET_ID', direction='like')")
    print("Swipe (bulk):", "call swipe_bulk(client, [{'user_id':'x','direction':'like'}])")
    print("AI chat (single):", "call ai_chat(client, 'Hi', thread_id='...')")
    print("AI chat (bulk):", "call ai_chat_bulk(client, [{'thread_id':'...','message':'...'}])")


if __name__ == "__main__":
    main()
