"""
Example: run auto-swipe using database-stored account data.

Usage (from backend): python -m examples.auto_swipe_example

Data sources:
- Headers, API base URL, and GraphQL paths: backend/sample.json
- Auth token, cookie_string, and proxy: MongoDB accounts collection
"""

import os
import sys
from typing import Any, Dict

from bson import ObjectId
from pymongo import MongoClient

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from okcupid_api import OkCupidClient  # noqa: E402
from okcupid_api import swipe  # noqa: E402
from okcupid_api.load_sample import (  # noqa: E402
    get_api,
    get_auth,
    get_graphql_settings,
    get_swipe_settings,
)


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
    # Start from sample.json headers + api config
    headers: Dict[str, str] = {}
    # Prefer the internal API host (GraphQL) so we mirror browser requests like
    # https://e2p-okapi.api.okcupid.com.
    base_url = os.getenv("OKCUPID_API_HOST") or os.getenv("OKCUPID_API_BASE")
    try:
        sample_auth = get_auth()
        sample_headers = sample_auth.get("headers") or {}
        if isinstance(sample_headers, dict):
            headers.update(
                {str(k): str(v) for k, v in sample_headers.items() if v is not None}
            )
        api_cfg = get_api()
        if isinstance(api_cfg, dict):
            api_host = api_cfg.get("api_host")
            web_base = api_cfg.get("base_url")
        else:
            api_host = None
            web_base = None
        # If there is no explicit env override, use the API host first, then fall
        # back to the web base URL.
        if not base_url:
            base_url = api_host or web_base
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


def main() -> None:
    db_account = _get_account_doc()
    client = _build_client_from_db_account(db_account)
    swipe_cfg = get_swipe_settings()
    gql_cfg = get_graphql_settings()
    # Support multiple directions in a single run:
    # Priority:
    #   1) SWIPE_DIRECTIONS env var (comma-separated)
    #   2) swipe.directions in sample.json (list)
    #   3) SWIPE_DIRECTION env var
    #   4) swipe.direction in sample.json (string, legacy)
    directions_env = os.getenv("SWIPE_DIRECTIONS")
    if directions_env:
        directions = [d.strip() for d in directions_env.split(",") if d.strip()]
    else:
        cfg_dirs = swipe_cfg.get("directions")
        if isinstance(cfg_dirs, list) and cfg_dirs:
            directions = [str(d).strip() for d in cfg_dirs if str(d).strip()]
        else:
            directions = [os.getenv("SWIPE_DIRECTION") or swipe_cfg.get("direction", "like")]

    max_swipes = int(os.getenv("MAX_SWIPES") or swipe_cfg.get("max_swipes", 10))
    like_pct = swipe_cfg.get("like_percentage")
    delay = float(os.getenv("SWIPE_DELAY") or swipe_cfg.get("delay_seconds", 1.5))
    discovery_path = gql_cfg.get("discovery_path") or None
    initial_stacks_path = gql_cfg.get("initial_stacks_path") or None
    swipe_path = gql_cfg.get("swipe_path") or None

    def on_swipe(user_id: str, dir: str, resp: dict) -> None:
        print(f"  {dir} -> {user_id}")

    def on_error(uid: str, err: Exception) -> None:
        print(f"  error for {uid}: {err}")

    totals: Dict[str, Any] = {}
    for direction in directions:
        # If both pass and like are present and like_percentage is set,
        # split the total max_swipes between them.
        dir_max = max_swipes
        if (
            isinstance(like_pct, (int, float))
            and "like" in directions
            and "pass" in directions
            and len(directions) == 2
        ):
            like_count = int(round(max_swipes * (float(like_pct) / 100.0)))
            like_count = max(0, min(max_swipes, like_count))
            pass_count = max_swipes - like_count
            if direction == "like":
                dir_max = like_count
            elif direction == "pass":
                dir_max = pass_count

        print(f"Auto-swipe: direction={direction}, max={dir_max}, delay={delay}s")
        summary = swipe.auto_swipe(
            client,
            direction=direction,
            max_swipes=dir_max,
            delay_seconds=delay,
            discovery_graphql_path=discovery_path,
            initial_stacks_path=initial_stacks_path,
            swipe_graphql_path=swipe_path,
            on_swipe=on_swipe,
            on_error=on_error,
        )
        totals[direction] = summary
        print(
            f"Done ({direction}): swiped={summary['swiped']}, skipped={summary['skipped']}, errors={summary['errors']}"
        )

    if len(directions) > 1:
        print("Summary by direction:")
        for d in directions:
            s = totals[d]
            print(f"  {d}: swiped={s['swiped']}, skipped={s['skipped']}, errors={s['errors']}")


if __name__ == "__main__":
    main()
