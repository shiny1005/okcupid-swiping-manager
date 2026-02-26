"""
Debug: print the exact URL and headers used for the discovery GraphQL request.
Run: python -m examples.debug_request
Use this to compare with DevTools and find why you get 403.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from okcupid_api import OkCupidClient


def _mask(v: str) -> str:
    if not v:
        return "(empty)"
    return (v[:20] + "...") if len(v) > 20 else v


def main() -> None:
    client = OkCupidClient.from_sample()
    from okcupid_api.load_sample import get_graphql_settings

    gql_cfg = get_graphql_settings()
    # Prefer operation-specific discovery path (e.g. /graphql/WebStackUsers)
    path = (gql_cfg.get("discovery_path") or "").strip() or "/graphql/"
    url = client._url(path)
    print("Request URL:", url)
    print()
    print("Headers (Cookie and Authorization masked):")
    for k, v in client._session.headers.items():
        if k.lower() in ("cookie", "authorization"):
            v = _mask(v)
        print(f"  {k}: {v}")
    print()
    # Actually perform the request and show response
    from okcupid_api.graphql_operations import DISCOVERY_FEED_QUERY

    try:
        r = client.graphql(
            DISCOVERY_FEED_QUERY,
            path=path,
            operation_name=None,
            variables={},
        )
        print("Response status:", r.status_code)
        print("Response headers:")
        for k, v in r.headers.items():
            print(f"  {k}: {v}")
        print("Response body (first 500 chars):", r.text[:500])
    except Exception as e:
        print("Exception:", e)
        resp = getattr(e, "response", None)
        if resp is not None:
            print("Response status code:", resp.status_code)
            print("Response body (first 500 chars):", (resp.text or "")[:500])


if __name__ == "__main__":
    main()
