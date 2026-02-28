"""
Auto-chat runner: processes OkCupid conversations and sends AI-powered replies.

Usage (from backend/):
    python -m examples.auto_chat_runner

Data sources:
- Headers, API base URL: backend/sample.json
- Auth token, cookie_string, proxy, and auto_chat/OpenAI settings: MongoDB
"""

import os
import sys
import time
from typing import Any, Dict

from bson import ObjectId
from pymongo import MongoClient

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover
    load_dotenv = lambda: None  # type: ignore[assignment]

from okcupid_api import OkCupidClient  # noqa: E402
from okcupid_api.ai_auto_chat import AutoChatConfig, auto_chat_once  # noqa: E402
from okcupid_api.load_sample import (  # noqa: E402
    get_api,
    get_auth,
    get_auto_chat_settings,
    get_openai_settings,
)


def get_merged_auto_chat_config(
    general_doc: Dict[str, Any] | None,
    openai_doc: Dict[str, Any] | None,
) -> tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Merge MongoDB config with sample.json fallbacks. Used by both the
    CLI runner and the API server.
    general_doc: from config collection {"_id": "general_settings", "auto_chat": {...}}
    openai_doc: from config collection {"_id": "openai_config", "apiKey": "...", "model": "..."}
    """
    auto_cfg: Dict[str, Any] = {}
    openai_cfg: Dict[str, Any] = {}

    if general_doc:
        ac = general_doc.get("auto_chat")
        if isinstance(ac, dict):
            auto_cfg.update(ac)
    if openai_doc:
        openai_cfg["api_key"] = openai_doc.get("apiKey")
        openai_cfg["model"] = openai_doc.get("model")

    try:
        for k, v in get_auto_chat_settings().items():
            auto_cfg.setdefault(k, v)
    except FileNotFoundError:
        pass
    try:
        for k, v in get_openai_settings().items():
            openai_cfg.setdefault(k, v)
    except FileNotFoundError:
        pass

    return auto_cfg, openai_cfg


def run_auto_chat_once_for_client(
    client: OkCupidClient,
    auto_cfg: Dict[str, Any],
    openai_cfg: Dict[str, Any],
) -> Any:
    """
    Shared helper: build AutoChatConfig from merged config dicts and run
    auto_chat_once. Used by both the CLI runner and the API server.
    """
    funnel = (os.getenv("AI_CHAT_FUNNEL") or "").strip() or str(
        auto_cfg.get("funnel") or ""
    ).strip()
    if not funnel:
        raise ValueError(
            "Snap funnel username required. Set AI_CHAT_FUNNEL env var or general settings auto_chat.funnel."
        )

    openai_api_key = (os.getenv("OPENAI_API_KEY") or "").strip() or str(
        openai_cfg.get("api_key") or ""
    ).strip()
    if not openai_api_key:
        raise ValueError(
            "OpenAI key required. Set OPENAI_API_KEY env var or configure it in the backend Settings page."
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
    return auto_chat_once(client, config=cfg)


def _get_db():
    uri = os.getenv(
        "MONGODB_URI",
        "mongodb+srv://mongodb1234:iamanetstar@cluster0.svpkyqh.mongodb.net/",
    )
    name = os.getenv("MONGODB_DB_NAME", "okcupid_automation")
    client = MongoClient(uri)
    return client[name]


def _get_account_doc() -> Dict[str, Any]:
    db = _get_db()
    col = db["accounts"]
    account_id = os.getenv("ACCOUNT_ID")
    if account_id:
        doc = col.find_one({"_id": ObjectId(account_id)})
    else:
        doc = col.find_one()
    if not doc:
        raise SystemExit("No accounts found in database. Create one from the UI first.")
    return doc


def _build_client_from_db_account(doc: Dict[str, Any]) -> OkCupidClient:
    headers: Dict[str, str] = {}
    base_url = os.getenv("OKCUPID_API_BASE")
    try:
        sample_auth = get_auth()
        sample_headers = sample_auth.get("headers") or {}
        if isinstance(sample_headers, dict):
            headers.update(
                {str(k): str(v) for k, v in sample_headers.items() if v is not None}
            )
        api_cfg = get_api()
        if not base_url:
            base_url = api_cfg.get("base_url")
    except Exception:
        pass

    auth_doc = doc.get("auth") or {}
    token = auth_doc.get("token")
    cookie_string = auth_doc.get("cookie_string") or (
        (auth_doc.get("cookies") or {}).get("cookie_string")
        if isinstance(auth_doc.get("cookies"), dict)
        else None
    )
    if token:
        headers["Authorization"] = (
            token if token.startswith("Bearer ") else f"Bearer {token}"
        )

    proxies: Dict[str, str] | None = None
    proxy_cfg = doc.get("proxy") or {}
    if isinstance(proxy_cfg, dict):
        host = (proxy_cfg.get("host") or "").strip()
        port = proxy_cfg.get("port")
        if host and port:
            ptype = (proxy_cfg.get("type") or "socks5").strip().lower() or "socks5"
            user = (proxy_cfg.get("username") or "").strip()
            password = (proxy_cfg.get("password") or "").strip()
            auth_part = f"{user}:{password}@" if user and password else ""
            url = f"{ptype}://{auth_part}{host}:{port}"
            proxies = {"http": url, "https": url}

    client = OkCupidClient(
        base_url=base_url,
        cookies=None,
        headers=headers or None,
        proxies=proxies,
    )
    if cookie_string:
        client.session.headers["Cookie"] = cookie_string
    return client


def _get_auto_chat_and_openai() -> tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Load auto_chat + openai settings from MongoDB config collection, with
    sample.json as a fallback.
    """
    db = _get_db()
    config_col = db["config"]
    auto_cfg: Dict[str, Any] = {}
    openai_cfg: Dict[str, Any] = {}

    try:
        general_doc = config_col.find_one({"_id": "general_settings"}) or {}
        auto_cfg = general_doc.get("auto_chat") or {}
    except Exception:
        auto_cfg = {}

    try:
        openai_doc = config_col.find_one({"_id": "openai_config"}) or {}
        openai_cfg = {
            "api_key": openai_doc.get("apiKey"),
            "model": openai_doc.get("model"),
        }
    except Exception:
        openai_cfg = {}

    # Fallback to sample.json when DB is missing values
    try:
        sample_auto = get_auto_chat_settings()
        for k, v in sample_auto.items():
            auto_cfg.setdefault(k, v)
    except FileNotFoundError:
        pass

    try:
        sample_openai = get_openai_settings()
        for k, v in sample_openai.items():
            openai_cfg.setdefault(k, v)
    except FileNotFoundError:
        pass

    return auto_cfg, openai_cfg


def main() -> None:
    load_dotenv()

    db_account = _get_account_doc()
    client = _build_client_from_db_account(db_account)
    auto_cfg, openai_cfg = _get_auto_chat_and_openai()

    interval = float(os.getenv("AI_CHAT_POLL_SECONDS") or auto_cfg.get("poll_seconds") or "20")
    print(f"Auto-chat started. Poll interval: {interval}s")

    while True:
        try:
            results = run_auto_chat_once_for_client(client, auto_cfg, openai_cfg)
            if results:
                for target_id, msgs in results:
                    print(f"Replied to {target_id}: {msgs}")
            else:
                print("No conversations needed replies.")
        except KeyboardInterrupt:
            print("Stopping auto-chat.")
            break
        except ValueError as e:
            raise SystemExit(str(e)) from e
        except Exception as e:  # pragma: no cover
            print("Error during auto_chat_once:", e)
        time.sleep(interval)


if __name__ == "__main__":
    main()

