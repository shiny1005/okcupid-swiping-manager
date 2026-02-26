"""
Profile: view individual profile and bulk fetch.
Endpoints and payloads to be filled after reverse engineering.
"""

from typing import Any, Dict, List, Optional

from okcupid_api.client import OkCupidClient
from okcupid_api.config import ENDPOINTS
from okcupid_api.graphql_operations import WEB_SETTINGS_PAGE_QUERY


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
    return resp.json()["data"]["me"]

