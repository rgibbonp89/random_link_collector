from enum import Enum
from pathlib import Path
from typing import Type, Tuple, Union
from google.cloud import firestore
from google.cloud.firestore_v1 import (
    CollectionReference,
    DocumentSnapshot,
)
from google.cloud.firestore_v1.client import Client

from bs4 import BeautifulSoup
from readability import Document
from requests import Session

from integrations.logins.parse_mail import get_message_content
import requests
import re
import pickle
from dotenv import load_dotenv
import os

load_dotenv()

CLEANR = re.compile("<.*?>")

db: Client = firestore.Client.from_service_account_json(
    f"{Path(__file__).parent.parent.parent.parent}/.keys/firebase.json"
)

doc_ref = db.collection("sessions")
FT_SESSION_ID = "ft_session"
SESSION_COOKIES_KEY = "session_cookies"


class ft_enum(Enum):
    search_query_gmail = """subject:'Your FT.com access code' after: {query}"""
    login_url = "https://accounts.ft.com/login"
    data = {
        "_csrf": None,
        "formType": "one-time-login-token",
        "formAction": "token-create",
        "email": os.environ.get("FT_EMAIL"),
        "rememberMe": "true",
        "siteKey": os.environ.get("FT_SITE_KEY"),
    }
    data_login_endpoint = {
        "_csrf": None,
        "formType": "one-time-login-token",
        "formAction": "login-with-token",
        "email": os.environ.get("FT_EMAIL"),
        "rememberMe": "true",
        "ssoTokenForm": "false",
        "location": "",
        "token": None,
    }


def _search_sessions_db_for_cookies(
    documents: CollectionReference, document_name: str
) -> Union[DocumentSnapshot, None]:
    return documents.document(document_name).get()


def _save_sessions_cookies_to_db(
    documents: CollectionReference,
    document_name: str,
    session_obj_name: str,
    session_obj: Session,
) -> None:
    pickled_cookies = pickle.dumps(session_obj.cookies)
    documents.document(document_name).set({session_obj_name: pickled_cookies})


def ft_authentication_and_parse_flow(
    news_source_configuration: Type[ft_enum],
    service,
    search_query: str,
    article_url: str,
) -> str:
    with requests.Session() as sess:
        session_doc = _search_sessions_db_for_cookies(doc_ref, FT_SESSION_ID)
        if session_doc.to_dict():
            cookies = session_doc.to_dict().get(SESSION_COOKIES_KEY)
            sess.cookies.update(pickle.loads(cookies))
        else:
            last_code_before_authenticating: str = get_message_content(
                service, search_query
            ).get("code")
            text = sess.get(news_source_configuration.login_url.value)
            doc = BeautifulSoup(text.text)
            _csrf = doc.find("input", value=True)["value"]
            news_source_configuration.data.value.update({"_csrf": _csrf})
            sess.post(
                news_source_configuration.login_url.value,
                news_source_configuration.data.value,
            )
            newest_code: str = get_message_content(service, search_query).get("code")
            while newest_code == last_code_before_authenticating:
                newest_code: str = get_message_content(service, search_query).get(
                    "code"
                )

            news_source_configuration.data_login_endpoint.value.update(
                {"_csrf": _csrf, "token": newest_code}
            )
            sess.post(
                news_source_configuration.login_url.value,
                news_source_configuration.data_login_endpoint.value,
            )
            _save_sessions_cookies_to_db(
                doc_ref, FT_SESSION_ID, SESSION_COOKIES_KEY, sess
            )
        article_text = sess.get(article_url)
        return re.sub(CLEANR, "", Document(article_text.text).summary())


class SiteAuthenticator(Enum):
    ft_authenticator = ft_authentication_and_parse_flow


def parse_article_url_for_correct_login_flow(
    article_url: str,
) -> Tuple[SiteAuthenticator, Type[ft_enum]]:
    if "ft.com" in article_url:
        return SiteAuthenticator.ft_authenticator, ft_enum
