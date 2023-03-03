from __future__ import print_function

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from pathlib import Path
from googleapiclient.discovery import build, Resource
import os

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
TOKEN_PATH = f"{Path(__file__).parent.parent.parent}/.keys/token.json"
GMAIL_KEY_PATH = f"{Path(__file__).parent.parent.parent}/.keys/credentials.json"
REDIRECT_URI = "http://localhost:8080"
PORT = 8080


def authenticate_user_and_provide_gmail_service() -> Resource:
    creds = None

    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                GMAIL_KEY_PATH, SCOPES, redirect_uri=REDIRECT_URI
            )
            creds = flow.run_local_server(port=PORT)
        with open(TOKEN_PATH, "w") as token:
            token.write(creds.to_json())
    service = build("gmail", "v1", credentials=creds)
    return service
