"""
Swipe: like/pass (single, bulk) and auto-swiping.
Endpoints and payloads to be filled after reverse engineering.
"""

import time
from typing import Any, Callable, Dict, List, Optional

from okcupid_api.client import OkCupidClient
from okcupid_api.config import ENDPOINTS


# Keys to try when extracting user id from a feed item (set first match from API)
USER_ID_KEYS = ("userid", "user_id", "id", "uid")

def _operation_from_graphql_path(graphql_path: Optional[str]) -> Optional[str]:
    """
    OkCupid routes GraphQL by URL path (e.g. /graphql/WebStackUsers).
    When provided, we default operationName to that last path segment so it matches the browser.
    """
    if not graphql_path:
        return None
    seg = graphql_path.strip("/").split("/")[-1].strip()
    return seg or None


def _user_id_from_item(item: Dict[str, Any]) -> Optional[str]:
    """Extract user id from a discovery/feed item. Adjust keys to match API."""
    if not isinstance(item, dict):
        return None
    # 1) Simple / flat ids on the item (userid, user_id, id, uid)
    for key in USER_ID_KEYS:
        val = item.get(key)
        if val is not None and val != "":
            return str(val)
    # 2) Nested WebStackUsers / MatchFragment-style: item.user.id
    user = item.get("user")
    if isinstance(user, dict):
        uid = user.get("id")
        if isinstance(uid, str) and uid:
            return uid
    # 3) Fallback for shapes like item.match.user.id
    match = item.get("match")
    if isinstance(match, dict):
        m_user = match.get("user")
        if isinstance(m_user, dict):
            uid = m_user.get("id")
            if isinstance(uid, str) and uid:
                return uid
    return None


def _graphql_list(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Unwrap list from GraphQL response: data.data.<operation> or data.data.<operation>.items etc."""
    inner = data.get("data") if isinstance(data, dict) else None
    if not isinstance(inner, dict):
        return []
    for _key, val in inner.items():
        if isinstance(val, list):
            return val
        if isinstance(val, dict):
            for k in ("items", "profiles", "results", "data", "feed", "edges"):
                if isinstance(val.get(k), list):
                    return val[k]
    return []


def _user_ids_from_stacks(data: Dict[str, Any]) -> List[str]:
    """
    Extract user ids from WebInitialStacksMenu response.

    Shape (simplified):
    data.me.stacks[].data[] -> StackMatch | FirstPartyAd | ThirdPartyAd
    For StackMatch items: item.match.user.id holds the user id.
    """
    ids: List[str] = []
    try:
        me = (data.get("data") or {}).get("me")
        if not isinstance(me, dict):
            return ids

        stacks = me.get("stacks") or []
        for stack in stacks:
            if not isinstance(stack, dict):
                continue
            items = stack.get("data") or []
            if not isinstance(items, list):
                continue
            for item in items:
                if not isinstance(item, dict):
                    continue
                if item.get("__typename") != "StackMatch":
                    continue
                match = item.get("match")
                if not isinstance(match, dict):
                    continue
                user = match.get("user")
                if not isinstance(user, dict):
                    continue
                uid = user.get("id")
                if uid and isinstance(uid, str):
                    ids.append(uid)
    except (KeyError, TypeError, AttributeError):
        # If the shape is slightly different, fail soft and return what we collected so far.
        pass
    return ids


def get_initial_stacks_user_ids(
    client: OkCupidClient,
    *,
    graphql_path: Optional[str] = None,
) -> List[str]:
    """
    Fetch WebInitialStacksMenu and extract user ids from stacks (data.match.user.id).
    Returns list of user ids to pass to WebStackUsers.
    """
    from okcupid_api.graphql_operations import WEB_INITIAL_STACKS_MENU_QUERY

    path = graphql_path or "/graphql/WebInitialStacksMenu"
    resp = client.graphql(
        WEB_INITIAL_STACKS_MENU_QUERY,
        path=path,
        operation_name="WebInitialStacksMenu",
        variables={},
    )
    resp.raise_for_status()
    return _user_ids_from_stacks(resp.json())


def get_candidates(
    client: OkCupidClient,
    *,
    limit: Optional[int] = None,
    variables: Optional[Dict[str, Any]] = None,
    graphql_path: Optional[str] = None,
    initial_stacks_path: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Fetch the next batch of profiles to swipe on.

    For WebStackUsers: first calls WebInitialStacksMenu to get user ids from stacks,
    then calls WebStackUsers with variables {userIds: [...]}.
    """
    from okcupid_api.graphql_operations import WEB_STACK_USERS_QUERY

    # WebStackUsers flow: get userIds from WebInitialStacksMenu, then fetch users
    stacks_path = initial_stacks_path or "/graphql/WebInitialStacksMenu"
    discovery_path = graphql_path or "/graphql/WebStackUsers"

    user_ids = get_initial_stacks_user_ids(
        client,
        graphql_path=stacks_path,
    )
    if not user_ids:
        return []

    variables = dict(variables or {})
    variables["userIds"] = user_ids[:limit] if limit is not None else user_ids

    resp = client.graphql(
        WEB_STACK_USERS_QUERY,
        path=discovery_path,
        operation_name=_operation_from_graphql_path(discovery_path) or "WebStackUsers",
        variables=variables,
    )
    resp.raise_for_status()
    body = resp.json() or {}
    me = (body.get("data") or {}).get("me") or {}
    raw_list = me.get("matches") or []
    items = raw_list[:limit] if limit is not None else raw_list
    return items


def swipe(
    client: OkCupidClient,
    target_user_id: str,
    *,
    direction: str = "like",  # or "pass" / "yes" / "no" – confirm from API
    extra: Optional[Dict[str, Any]] = None,
    graphql_path: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Single swipe (like or pass) on a profile. Uses GraphQL mutation.
    Variable names (userid, direction) – adjust to match DevTools payload.
    """
    from okcupid_api.graphql_operations import SWIPE_MUTATION

    variables = {
        "userid": target_user_id,
        "direction": direction,
        **(extra or {}),
    }
    resp = client.graphql(
        SWIPE_MUTATION,
        path=graphql_path,
        operation_name=_operation_from_graphql_path(graphql_path) or ENDPOINTS.swipe,
        variables=variables,
    )
    resp.raise_for_status()
    return resp.json()


def swipe_bulk(
    client: OkCupidClient,
    actions: List[Dict[str, Any]],
    *,
    key_user_id: str = "user_id",
    key_direction: str = "direction",
) -> List[Dict[str, Any]]:
    """
    Multiple swipes: one GraphQL call per action (or replace with batch mutation when available).
    """
    results = []
    for a in actions:
        uid = a.get(key_user_id)
        direction = a.get(key_direction, "like")
        if not uid:
            continue
        try:
            out = swipe(client, uid, direction=direction)
            results.append(out)
        except Exception:
            results.append({"error": True})
    return results


def auto_swipe(
    client: OkCupidClient,
    direction: str = "like",
    *,
    max_swipes: Optional[int] = None,
    delay_seconds: float = 1.0,
    batch_size: Optional[int] = None,
    discovery_graphql_path: Optional[str] = None,
    initial_stacks_path: Optional[str] = None,
    swipe_graphql_path: Optional[str] = None,
    filter_fn: Optional[Callable[[Dict[str, Any]], bool]] = None,
    on_swipe: Optional[Callable[[str, str, Dict[str, Any]], None]] = None,
    on_error: Optional[Callable[[str, Exception], None]] = None,
) -> Dict[str, Any]:
    """
    Automatically swipe through the discovery feed.

    - direction: "like" or "pass" (use exact values from API).
    - max_swipes: stop after this many swipes (None = no limit).
    - delay_seconds: seconds to wait between each swipe (rate limiting).
    - batch_size: how many candidates to fetch per batch (None = use API default).
    - filter_fn: optional(item) -> bool; only swipe if True (e.g. filter by age).
    - on_swipe: optional(user_id, direction, response) callback after each swipe.
    - on_error: optional(user_id, exception) callback on swipe failure.

    Returns summary: { "swiped": int, "skipped": int, "errors": int, "results": [...] }.
    """
    swiped = 0
    skipped = 0
    errors = 0
    results: List[Dict[str, Any]] = []

    while True:
        if max_swipes is not None and swiped >= max_swipes:
            break
        fetch_count = (batch_size if batch_size is not None else 20)
        if max_swipes is not None:
            fetch_count = min(fetch_count, max_swipes - swiped)

        try:
            items = get_candidates(
                client,
                limit=fetch_count,
                graphql_path=discovery_graphql_path,
                initial_stacks_path=initial_stacks_path,
            )
        except Exception as e:
            if on_error:
                on_error("(get_candidates)", e)
            errors += 1
            break
        if not items:
            break

        for item in items:
            if max_swipes is not None and swiped >= max_swipes:
                break
            user_id = _user_id_from_item(item)
            if not user_id:
                skipped += 1
                continue
            # Log every scraped user id to the console
            print(f"candidate -> {user_id}")
            if filter_fn is not None and not filter_fn(item):
                skipped += 1
                continue
            try:
                resp = swipe(
                    client,
                    user_id,
                    direction=direction,
                    graphql_path=swipe_graphql_path,
                )
                swiped += 1
                results.append({"user_id": user_id, "direction": direction, "response": resp})
                if on_swipe:
                    on_swipe(user_id, direction, resp)
            except Exception as e:
                errors += 1
                if on_error:
                    on_error(user_id, e)
                results.append({"user_id": user_id, "direction": direction, "error": str(e)})

            if delay_seconds > 0:
                time.sleep(delay_seconds)

    return {
        "swiped": swiped,
        "skipped": skipped,
        "errors": errors,
        "results": results,
    }
