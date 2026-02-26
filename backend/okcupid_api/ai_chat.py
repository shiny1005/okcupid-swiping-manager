"""
AI Chat: send/receive AI chat messages – single and bulk.
Endpoints and payloads to be filled after reverse engineering.
"""

from typing import Any, Dict, List, Optional

from okcupid_api.client import OkCupidClient
from okcupid_api.config import ENDPOINTS


def ai_chat(
    client: OkCupidClient,
    message: str,
    *,
    thread_id: Optional[str] = None,
    user_id: Optional[str] = None,
    extra: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Send one AI chat message (and optionally get response).
    Replace path and body with actual API (e.g. conversation_id, message content key).
    """
    path = ENDPOINTS.ai_chat
    body = {"message": message, **(extra or {})}
    if thread_id is not None:
        body["thread_id"] = thread_id
    if user_id is not None:
        body["user_id"] = user_id
    resp = client.post(path, json=body)
    resp.raise_for_status()
    return resp.json()


def ai_chat_bulk(
    client: OkCupidClient,
    requests_list: List[Dict[str, Any]],
    *,
    key_message: str = "message",
    key_thread_id: str = "thread_id",
) -> List[Dict[str, Any]]:
    """
    Send multiple AI chat messages (or open multiple threads) in one/batched request(s).
    requests_list: [{"thread_id": "...", "message": "..."}, ...].
    """
    path = ENDPOINTS.ai_chat_bulk
    payload = [
        {key_thread_id: r.get(key_thread_id), key_message: r.get(key_message)}
        for r in requests_list
    ]
    resp = client.post(path, json={"messages": payload})
    resp.raise_for_status()
    data = resp.json()
    return data.get("results", data.get("data", []))
