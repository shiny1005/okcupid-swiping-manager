"""
Auto-chat runner: processes OkCupid conversations and sends AI-powered replies.

Usage (from backend/):
    python -m examples.auto_chat_runner

Environment:
    OPENAI_API_KEY   - required, for OpenAI chat completions
    OKCUPID_*        - or use sample.json with OkCupidClient.from_sample()
"""

import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover
    load_dotenv = lambda: None  # type: ignore[assignment]

from okcupid_api import OkCupidClient
from okcupid_api.ai_auto_chat import AutoChatConfig, auto_chat_once
from okcupid_api.load_sample import get_auto_chat_settings, get_openai_settings


def main() -> None:
    load_dotenv()

    try:
        client = OkCupidClient.from_sample()
        auto_cfg = get_auto_chat_settings()
        openai_cfg = get_openai_settings()
    except FileNotFoundError:
        base = os.getenv("OKCUPID_API_BASE", "https://www.okcupid.com")
        cookies = {}
        for k, v in os.environ.items():
            if k.startswith("OKCUPID_COOKIE_"):
                cookies[k.replace("OKCUPID_COOKIE_", "", 1)] = v
        client = OkCupidClient(base_url=base, cookies=cookies or None)
        auto_cfg = {}
        openai_cfg = {}

    funnel = (os.getenv("AI_CHAT_FUNNEL") or "").strip() or str(auto_cfg.get("funnel") or "").strip()
    if not funnel:
        raise SystemExit(
            "Snap funnel username required. Set AI_CHAT_FUNNEL env var or sample.json auto_chat.funnel."
        )

    openai_api_key = (os.getenv("OPENAI_API_KEY") or "").strip() or str(openai_cfg.get("api_key") or "").strip()
    if not openai_api_key:
        raise SystemExit(
            "OpenAI key required. Set OPENAI_API_KEY env var or sample.json openai.api_key."
        )

    cfg = AutoChatConfig(
        funnel=funnel,
        openai_api_key=openai_api_key,
        cta_min_msgs=int(auto_cfg.get("cta_min_msgs", 2) or 2),
        cta_max_msgs=int(auto_cfg.get("cta_max_msgs", 4) or 4),
        delay_chat_part_min=float(auto_cfg.get("delay_chat_part_min", 1.0) or 1.0),
        delay_chat_part_max=float(auto_cfg.get("delay_chat_part_max", 3.0) or 3.0),
        model=str(openai_cfg.get("model") or "gpt-4o-mini"),
    )

    interval = float(os.getenv("AI_CHAT_POLL_SECONDS") or auto_cfg.get("poll_seconds") or "20")
    print(f"Auto-chat started. Poll interval: {interval}s")

    while True:
        try:
            results = auto_chat_once(client, config=cfg)
            if results:
                for target_id, msgs in results:
                    print(f"Replied to {target_id}: {msgs}")
            else:
                print("No conversations needed replies.")
        except KeyboardInterrupt:
            print("Stopping auto-chat.")
            break
        except Exception as e:  # pragma: no cover
            print("Error during auto_chat_once:", e)
        time.sleep(interval)


if __name__ == "__main__":
    main()

