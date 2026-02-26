from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from okcupid_api.client import OkCupidClient
from okcupid_api.graphql_operations import (
    WEB_ME_QUERY,
    WEB_GET_MESSAGES_MAIN_QUERY,
    WEB_CONVERSATION_THREAD_QUERY,
    WEB_CONVERSATION_MESSAGE_SEND_MUTATION,
)


@dataclass
class Me:
    id: str
    displayname: str


def get_me(client: OkCupidClient) -> Me:
    resp = client.graphql(
        WEB_ME_QUERY,
        path="/graphql/WebMe",
        operation_name="WebMe",
        variables={},
    )
    resp.raise_for_status()
    data = resp.json()["data"]["me"]
    return Me(id=data["id"], displayname=data.get("displayname") or "")


def get_conversations_main(
    client: OkCupidClient,
    *,
    userid: str,
    filter_value: str = "ALL",
    after: Optional[str] = None,
) -> Dict[str, Any]:
    variables: Dict[str, Any] = {"userid": userid, "filter": filter_value}
    if after is not None:
        variables["after"] = after
    resp = client.graphql(
        WEB_GET_MESSAGES_MAIN_QUERY,
        path="/graphql/WebGetMessagesMain",
        operation_name="WebGetMessagesMain",
        variables=variables,
    )
    resp.raise_for_status()
    return resp.json()["data"]["user"]


def get_conversation_thread(
    client: OkCupidClient,
    *,
    target_id: str,
    limit: Optional[int] = None,
    before: Optional[str] = None,
    is_polled: bool = False,
) -> Dict[str, Any]:
    variables: Dict[str, Any] = {"targetId": target_id, "isPolled": is_polled}
    if limit is not None:
        variables["limit"] = limit
    if before is not None:
        variables["before"] = before
    resp = client.graphql(
        WEB_CONVERSATION_THREAD_QUERY,
        path="/graphql/WebConversationThread",
        operation_name="WebConversationThread",
        variables=variables,
    )
    resp.raise_for_status()
    return resp.json()["data"]["me"]["conversationThread"]


def send_message(
    client: OkCupidClient,
    *,
    target_id: str,
    text: str,
    source: str = "desktop_global",
) -> Dict[str, Any]:
    variables = {"input": {"targetId": target_id, "text": text, "source": source}}
    resp = client.graphql(
        WEB_CONVERSATION_MESSAGE_SEND_MUTATION,
        path="/graphql/WebConversationMessageSend",
        operation_name="WebConversationMessageSend",
        variables=variables,
    )
    resp.raise_for_status()
    return resp.json()["data"]["conversationMessageSend"]


