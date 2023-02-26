from enum import Enum
from functools import partial
from pathlib import Path
from typing import Type, Tuple, Union, Dict, Callable
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
SESSION_COOKIES_KEY = "session_cookies"


def _ft_message_extractor(message, text) -> Dict[str, str]:
    code = re.findall(r"\*.*?\*(?!\.\S)", text.text)[0].replace("*", "")
    return {"code": code, "date": message.get("internalDate")}


def _substack_message_extractor(message, text) -> Dict[str, str]:
    code = re.findall(r"\*.*?\*(?!\.\S)", text.text)[0].replace("*", "")
    return {"code": code, "date": message.get("internalDate")}


def _parse_message_for_ft_login_flow(
    news_source_configuration, service, sess, search_query
) -> Session:
    last_code_before_authenticating: str = get_message_content(
        service,
        search_query,
        _publication_specific_message_details_fn=news_source_configuration.message_extractor,
    ).get("code")
    text = sess.get(news_source_configuration.login_url.value)
    doc = BeautifulSoup(text.text)
    _csrf = doc.find("input", value=True)["value"]
    news_source_configuration.data.value.update({"_csrf": _csrf})
    sess.post(
        news_source_configuration.login_url.value,
        news_source_configuration.data.value,
    )
    newest_code: str = get_message_content(
        service,
        search_query,
        _publication_specific_message_details_fn=news_source_configuration.message_extractor,
    ).get("code")
    while newest_code == last_code_before_authenticating:
        newest_code: str = get_message_content(
            service,
            search_query,
            _publication_specific_message_details_fn=news_source_configuration.message_extractor,
        ).get("code")
    news_source_configuration.data_login_endpoint.value.update(
        {"_csrf": _csrf, "token": newest_code}
    )
    sess.post(
        news_source_configuration.login_url.value,
        news_source_configuration.data_login_endpoint.value,
    )
    _save_sessions_cookies_to_db(
        doc_ref,
        news_source_configuration.firestore_session_id.value,
        SESSION_COOKIES_KEY,
        sess,
    )
    return sess


def _parse_message_for_substack_login_flow(
    news_source_configuration, service, sess, search_query
):
    # get last email containing a code (its ID, probably)
    # request a new code (POST call to substack_enum.login_url using data_login)
    # wait for new email to come in
    # search for this tag data-saferedirecturl in mail html and make into fn (_substack_message_extractor)
    # make a get request to this link
    # save session obj
    pass


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
    message_extractor = _ft_message_extractor
    message_parser_for_login_flow = _parse_message_for_ft_login_flow
    firestore_session_id = "ft_session"


class substack_enum(Enum):
    search_query_gmail = """subject:"Sign in to Substack" after: {query}"""
    login_url = "https://substack.com/api/v1/email-login"
    data_login = {
        "redirect": "/",
        "for_pub": "",
        "email": os.environ.get("SUBSTACK_EMAIL"),
        "captcha_response": "null",
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


def authentication_and_parse_flow(
    news_source_configuration: Type[ft_enum],
    service,
    article_url: str,
    search_query: str,
) -> str:
    with requests.Session() as sess:
        session_doc = _search_sessions_db_for_cookies(
            doc_ref, news_source_configuration.firestore_session_id.value
        )
        if session_doc.to_dict():
            cookies = session_doc.to_dict().get(SESSION_COOKIES_KEY)
            sess.cookies.update(pickle.loads(cookies))
        else:
            news_source_configuration.message_parser_for_login_flow(
                news_source_configuration, service, sess, search_query
            )
        article_text = sess.get(article_url)
        return re.sub(CLEANR, "", Document(article_text.text).summary())


class SiteAuthenticator(Enum):
    ft_authenticator = partial(
        authentication_and_parse_flow, news_source_configuration=ft_enum
    )
    substack_authenticator = partial(
        authentication_and_parse_flow, news_source_configuration=substack_enum
    )


def parse_article_url_for_correct_login_flow(
    article_url: str,
) -> Tuple[SiteAuthenticator, Union[Type[ft_enum], Type[substack_enum]]]:
    if "ft.com" in article_url:
        return SiteAuthenticator.ft_authenticator, ft_enum
    if "substack.com" in article_url:
        return SiteAuthenticator.substack_authenticator, substack_enum
