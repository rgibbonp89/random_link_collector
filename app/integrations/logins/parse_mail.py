from __future__ import print_function

import base64
from typing import Dict, Callable
from googleapiclient.discovery import Resource


def get_message_content(
    service: Resource,
    mail_search_query: str,
    _publication_specific_message_details_fn: Callable,
) -> Dict[str, str]:
    messages = (
        service.users()
        .messages()
        .list(
            userId="me",
            q=mail_search_query,
        )
        .execute()
    )
    messages_metadata = messages.get("messages")
    codes_and_timestamps = []
    for metadata in messages_metadata:
        messageId = metadata.get("id")
        message = service.users().messages().get(userId="me", id=messageId).execute()
        message_first_part = (
            message["payload"]["parts"][0]
            if "parts" in list(message.keys())
            else message["payload"]
        )
        msg_str = base64.urlsafe_b64decode(
            message_first_part["body"]["data"].encode("ASCII")
        )
        codes_and_timestamps.append(
            _publication_specific_message_details_fn(msg_str, message)
        )
    return sorted(codes_and_timestamps, key=lambda x: x.get("date"))[-1]
