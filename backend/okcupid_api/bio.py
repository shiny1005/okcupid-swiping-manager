"""
Bio: edit profile bio – single and bulk.
Endpoints and payloads to be filled after reverse engineering.
"""

from typing import Any, Dict, List, Optional

from okcupid_api.client import OkCupidClient
from okcupid_api.config import ENDPOINTS


def edit_bio(
    client: OkCupidClient,
    bio_text: str,
    *,
    user_id: Optional[str] = None,
    extra: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Update bio for the current user (or given user_id if API supports).
    Replace path and body keys with actual API shape.
    """
    path = ENDPOINTS.bio_edit
    body = {"bio": bio_text, **(extra or {})}
    if user_id is not None:
        body["user_id"] = user_id
    resp = client.patch(path, json=body)
    resp.raise_for_status()
    return resp.json()


def edit_bio_bulk(
    client: OkCupidClient,
    updates: List[Dict[str, Any]],
    *,
    key_bio: str = "bio",
    key_user_id: str = "user_id",
) -> List[Dict[str, Any]]:
    """
    Update bios for multiple users (or multiple sections) in one/batched request(s).
    updates: list of {"user_id": "...", "bio": "..."} or similar – adjust to real API.
    """
    path = ENDPOINTS.bio_bulk
    payload = [
        {key_user_id: u.get(key_user_id), key_bio: u.get(key_bio)}
        for u in updates
    ]
    resp = client.post(path, json={"updates": payload})
    resp.raise_for_status()
    data = resp.json()
    return data.get("results", data.get("data", []))
