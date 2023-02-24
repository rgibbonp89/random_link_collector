from __future__ import print_function

import base64
import re
from datetime import date, timedelta
from typing import Dict

from bs4 import BeautifulSoup
from googleapiclient.discovery import Resource
from readability import Document


def get_message_content(service: Resource) -> Dict[str, str]:
    today = date.today()
    window = today - timedelta(days=1)
    messages = (
        service.users()
        .messages()
        .list(
            userId="me",
            q=f"""subject:'Your FT.com access code' after: {window.strftime('%Y/%m/%d')}""",
        )
        .execute()
    )
    messages_metadata = messages.get("messages")
    codes_and_timestamps = []
    for metadata in messages_metadata:
        messageId = metadata.get("id")
        message = service.users().messages().get(userId="me", id=messageId).execute()
        msg_str = base64.urlsafe_b64decode(
            message["payload"]["parts"][0]["body"]["data"].encode("ASCII")
        )
        text = BeautifulSoup(Document(msg_str).summary())
        code = re.findall(r"\*.*?\*(?!\.\S)", text.text)[0].replace("*", "")
        codes_and_timestamps.append({"code": code, "date": message.get("internalDate")})
    return sorted(codes_and_timestamps, key=lambda x: x.get("date"))[-1]
