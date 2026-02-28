"""
Profile: view individual profile and bulk fetch.
Endpoints and payloads to be filled after reverse engineering.
"""

from typing import Any, Dict, List, Optional

from okcupid_api.client import OkCupidClient
from okcupid_api.config import ENDPOINTS
from okcupid_api.graphql_operations import (
    WEB_SETTINGS_PAGE_QUERY,
    WEB_PROFILE_SELF_QUERY,
    UPDATE_ESSAY_MUTATION,
    WEB_UPDATE_REALNAME_MUTATION,
)


def get_profile(client: OkCupidClient, user_id: str) -> Dict[str, Any]:
    """
    Fetch a single profile by user_id.
    Replace path and response parsing with actual API shape.
    """
    path = ENDPOINTS.profile_view.format(user_id=user_id)
    resp = client.get(path)
    resp.raise_for_status()
    # TODO: map real response to a consistent schema
    return resp.json()


def get_profiles_bulk(
    client: OkCupidClient,
    user_ids: List[str],
    *,
    extra_params: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    """
    Fetch multiple profiles in one (or batched) request(s).
    Exact endpoint (POST body vs GET query) to be determined from Network tab.
    """
    # Placeholder: might be GET ?ids=1,2,3 or POST {"user_ids": [...]}
    path = ENDPOINTS.profile_bulk
    params = extra_params or {}
    # Option A: GET with comma-separated or repeated ids
    # params["ids"] = ",".join(user_ids)
    # resp = client.get(path, params=params)
    # Option B: POST body
    resp = client.post(path, json={"user_ids": user_ids, **params})
    resp.raise_for_status()
    data = resp.json()
    # TODO: extract list of profiles from real response (e.g. data["profiles"])
    if isinstance(data, list):
        return data
    return data.get("profiles", data.get("data", []))


def get_my_profile_settings(client: OkCupidClient) -> Dict[str, Any]:
    """
    Fetch your own profile/settings info using the WebSettingsPage GraphQL query.
    Returns the `me` object from the response.
    """
    resp = client.graphql(
        WEB_SETTINGS_PAGE_QUERY,
        path="/graphql/WebSettingsPage",
        operation_name="WebSettingsPage",
        variables={},
    )
    resp.raise_for_status()
    return resp.json().get("data", {}).get("me")


def get_my_bio(
    client: OkCupidClient,
    user_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Fetch your own bio (essay) using WebProfileSelf.
    Returns dict with keys: text (bio string or None), essay (full essay dict), user (raw user dict).
    """
    if not user_id:
        try:
            from okcupid_api.conversations import get_me
        except Exception:
            me = None
        else:
            try:
                me = get_me(client)
            except Exception:
                me = None
        if me is not None:
            user_id = getattr(me, "id", None)
    if not user_id:
        raise ValueError("user_id is required to fetch profile bio.")

    resp = client.graphql(
        WEB_PROFILE_SELF_QUERY,
        path="/graphql/WebProfileSelf",
        operation_name="WebProfileSelf",
        variables={"id": user_id},
    )
    resp.raise_for_status()
    user = resp.json().get("data", {}).get("user")
    if not user:
        return {"text": None, "essay": None, "user": None, "avatar_url": None}

    essays = (
        user.get("essaysWithDefaultsAndUniqueIds")
        or user.get("allEssays")
        or []
    )
    bio_essay: Optional[Dict[str, Any]] = None
    for e in essays:
        if e.get("groupTitle") == "About Me" or e.get("title") == "My self-summary":
            bio_essay = e
            break
    if bio_essay is None and essays:
        bio_essay = essays[0]

    if bio_essay is None:
        # No essay but we might still have an avatar
        photos = user.get("photos") or []
        avatar_url = None
        if photos:
            for p in photos:
                avatar_url = p.get("square400") or p.get("original")
                if avatar_url:
                    break
        return {"text": None, "essay": None, "user": user, "avatar_url": avatar_url}

    text = bio_essay.get("rawContent") or bio_essay.get("processedContent")
    photos = user.get("photos") or []
    avatar_url = None
    if photos:
        for p in photos:
            avatar_url = p.get("square400") or p.get("original")
            if avatar_url:
                break
    return {"text": text, "essay": bio_essay, "user": user, "avatar_url": avatar_url}


def update_my_bio(
    client: OkCupidClient,
    new_text: str,
    user_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Update your bio text using the updateEssay mutation.
    It first fetches WebProfileSelf to discover essayId and groupId for your bio,
    then calls updateEssay with essayContent=new_text.
    Returns the updated essay dict from the response.
    """
    info = get_my_bio(client, user_id=user_id)
    essay = info.get("essay")
    if not essay:
        raise ValueError("Could not locate bio essay to update from WebProfileSelf.")

    essay_id = essay.get("id")
    group_id = essay.get("groupId", "0")
    if not essay_id:
        raise ValueError("Bio essay is missing an id; cannot update.")

    variables = {
        "input": {
            "essayContent": new_text,
            "essayId": essay_id,
            "groupId": str(group_id),
        }
    }
    resp = client.graphql(
        UPDATE_ESSAY_MUTATION,
        path="/graphql/updateEssay",
        operation_name="updateEssay",
        variables=variables,
    )
    resp.raise_for_status()
    data = resp.json().get("data", {}).get("essayUpdate", {})
    return data.get("essay") or data


def update_realname(client: OkCupidClient, realname: str) -> Dict[str, Any]:
    """
    Update your real name using WebUpdateRealname.
    """
    variables = {"input": {"realname": realname}}
    resp = client.graphql(
        WEB_UPDATE_REALNAME_MUTATION,
        path="/graphql/WebUpdateRealname",
        operation_name="WebUpdateRealname",
        variables=variables,
    )
    resp.raise_for_status()
    return resp.json().get("data", {}).get("userUpdateRealname", {})

