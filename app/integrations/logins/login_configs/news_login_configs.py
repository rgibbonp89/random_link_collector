import re
import os
from typing import Dict

from bs4 import BeautifulSoup
from dotenv import load_dotenv
from google.cloud.firestore_v1 import CollectionReference
from googleapiclient.discovery import Resource
from readability import Document
from requests import Session

from .base_login_config import SiteConfig
from integrations.logins.login_configs.parse_mail import get_message_content
from integrations.logins.login_configs.utils import (
    _save_sessions_cookies_to_db,
    SESSION_COOKIES_KEY,
)


load_dotenv()

FT_DATA_LOGIN_REDIRECT = {
    "_csrf": None,
    "formType": "one-time-login-token",
    "formAction": "token-create",
    "email": os.environ.get("FT_EMAIL"),
    "rememberMe": "true",
    "siteKey": os.environ.get("FT_SITE_KEY"),
}

FT_DATA_LOGIN_ENDPOINT = {
    "_csrf": None,
    "formType": "one-time-login-token",
    "formAction": "login-with-token",
    "email": os.environ.get("FT_EMAIL"),
    "rememberMe": "true",
    "ssoTokenForm": "false",
    "location": "",
    "token": None,
}

SUBSTACK_DATA_LOGIN_REDIRECT = {
    "redirect": "/",
    "for_pub": "",
    "email": os.environ.get("SUBSTACK_EMAIL"),
    "captcha_response": "null",
}


class FTLoginConfig(SiteConfig):
    search_query_gmail = """subject:'Your FT.com access code' after: {query}"""
    login_url = "https://accounts.ft.com/login"
    firestore_session_id = "ft_session"
    data_login_redirect = FT_DATA_LOGIN_REDIRECT
    data_login_endpoint = FT_DATA_LOGIN_ENDPOINT

    def extract_login_code_from_mail(
        self, msg_str: str, message: Resource
    ) -> Dict[str, str]:
        text = BeautifulSoup(Document(msg_str).summary())
        code = re.findall(r"\*.*?\*(?!\.\S)", text.text)[0].replace("*", "")
        return {"code": code, "date": message.get("internalDate")}

    def request_code_for_login_and_create_session(
        self,
        service: Resource,
        search_query: str,
        sess: Session,
        doc_ref: CollectionReference,
    ) -> Session:
        last_code_before_authenticating: str = get_message_content(
            service,
            search_query,
            _publication_specific_message_details_fn=self.extract_login_code_from_mail,
        ).get("code")
        text = sess.get(self.login_url)
        doc = BeautifulSoup(text.text)
        _csrf = doc.find("input", value=True)["value"]
        self.data_login_redirect.update({"_csrf": _csrf})
        sess.post(
            self.login_url,
            self.data_login_redirect,
        )
        newest_code: str = get_message_content(
            service,
            search_query,
            _publication_specific_message_details_fn=self.extract_login_code_from_mail,
        ).get("code")
        while newest_code == last_code_before_authenticating:
            newest_code: str = get_message_content(
                service,
                search_query,
                _publication_specific_message_details_fn=self.extract_login_code_from_mail,
            ).get("code")
        self.data_login_endpoint.update({"_csrf": _csrf, "token": newest_code})
        sess.post(
            self.login_url,
            self.data_login_endpoint,
        )
        _save_sessions_cookies_to_db(
            doc_ref,
            self.firestore_session_id,
            SESSION_COOKIES_KEY,
            sess,
        )
        return sess


class SubstackLoginConfig(SiteConfig):
    search_query_gmail = """subject:"Sign in to Substack" after: {query}"""
    login_url = "https://substack.com/api/v1/email-login"
    firestore_session_id = "substack_session"
    data_login_redirect = SUBSTACK_DATA_LOGIN_REDIRECT

    def extract_login_code_from_mail(
        self, msg_str: str, message: Resource
    ) -> Dict[str, str]:
        code = (
            BeautifulSoup(msg_str, "html")
            .find_all("a", attrs={"href": re.compile("^https://")})[0]
            .get("href")
        )
        return {"code": code, "date": message.get("internalDate")}

    def request_code_for_login_and_create_session(
        self,
        service: Resource,
        search_query: str,
        sess: Session,
        doc_ref: CollectionReference,
    ) -> Session:
        last_code_before_authenticating: str = get_message_content(
            service,
            search_query,
            _publication_specific_message_details_fn=self.extract_login_code_from_mail,
        ).get("code")
        sess.post(
            self.login_url,
            self.data_login_redirect,
        )
        newest_code: str = get_message_content(
            service,
            search_query,
            _publication_specific_message_details_fn=self.extract_login_code_from_mail,
        ).get("code")
        while newest_code == last_code_before_authenticating:
            newest_code: str = get_message_content(
                service,
                search_query,
                _publication_specific_message_details_fn=self.extract_login_code_from_mail,
            ).get("code")
        sess.get(newest_code)
        _save_sessions_cookies_to_db(
            doc_ref,
            self.firestore_session_id,
            SESSION_COOKIES_KEY,
            sess,
        )
        return sess
