from enum import Enum
from functools import partial
from typing import Type, Callable, Tuple

from bs4 import BeautifulSoup
from readability import Document

from integrations.logins.parse_mail import get_message_content
import requests
import re

CLEANR = re.compile("<.*?>")


class ft_enum(Enum):
    search_query_gmail = """subject:'Your FT.com access code' after: {query}"""
    login_url = "https://accounts.ft.com/login"
    data = {
        "_csrf": None,
        "formType": "one-time-login-token",
        "formAction": "token-create",
        "email": "rprice1989aws@gmail.com",
        "rememberMe": "true",
        "siteKey": "ab5cba1f-f466-4cc5-bcc3-a77be0a9c5df",
    }
    data_login_endpoint = {
        "_csrf": None,
        "formType": "one-time-login-token",
        "formAction": "login-with-token",
        "email": "rprice1989aws@gmail.com",
        "rememberMe": "true",
        "ssoTokenForm": "false",
        "location": "",
        "token": None,
    }


def ft_authentication_and_parse_flow(
    news_source_configuration: Type[ft_enum],
    service,
    search_query: str,
    article_url: str,
) -> str:
    with requests.Session() as sess:
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
            newest_code: str = get_message_content(service, search_query).get("code")

        news_source_configuration.data_login_endpoint.value.update(
            {"_csrf": _csrf, "token": newest_code}
        )
        sess.post(
            news_source_configuration.login_url.value,
            news_source_configuration.data_login_endpoint.value,
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
