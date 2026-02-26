"""
Configuration and discovered API endpoints.
OkCupid uses GraphQL: all requests go to https://e2p-okapi.api.okcupid.com/graphql/
"""

import os
from dataclasses import dataclass
from typing import Optional

# Web base (for reference / Origin if needed)
API_BASE = os.getenv("OKCUPID_API_BASE", "https://www.okcupid.com")
# GraphQL API – all Network requests use this host
API_HOST = os.getenv("OKCUPID_API_HOST", "https://e2p-okapi.api.okcupid.com")
# GraphQL endpoint path (single URL for all operations)
GRAPHQL_PATH = os.getenv("OKCUPID_GRAPHQL_PATH", "/graphql/")


@dataclass(frozen=True)
class Endpoints:
    """
    GraphQL: all operations POST to GRAPHQL_PATH. Names below are operation identifiers
    (operationName / query) to be filled from DevTools – request body has query, operationName, variables.
    """

    # Auth / session (if needed beyond cookies)
    login: str = "Login"
    session: str = "Session"

    # Profile – GraphQL operation names (replace with real from Network)
    profile_view: str = "ProfileView"
    profile_bulk: str = "ProfileBulk"

    # Bio
    bio_edit: str = "EditBio"
    bio_bulk: str = "EditBioBulk"

    # Swipe (like/pass) – mutations
    swipe: str = "LikeOrPass"
    swipe_bulk: str = "LikeOrPassBulk"
    discovery_feed: str = "DiscoveryFeed"

    # AI Chat
    ai_chat: str = "AIChat"
    ai_chat_bulk: str = "AIChatBulk"

    @property
    def base_url(self) -> str:
        return API_HOST.rstrip("/") if API_HOST else API_BASE.rstrip("/")

    @property
    def graphql(self) -> str:
        path = GRAPHQL_PATH.strip("/")
        return f"/{path}/" if path else "/graphql/"


ENDPOINTS = Endpoints()
