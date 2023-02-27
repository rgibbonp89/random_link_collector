from enum import Enum
from functools import partial
from typing import Type, Tuple, Union, Optional, Callable
from googleapiclient.discovery import Resource

from readability import Document

from integrations.logins.site_specific_login_config import (
    _search_sessions_db_for_cookies,
    ft_enum,
    substack_enum,
    doc_ref,
    SESSION_COOKIES_KEY,
)
import requests
import re
import pickle

CLEANR = re.compile("<.*?>")


def authentication_and_parse_flow(
    article_url: str,
    news_source_configuration: Optional[Type[ft_enum]] = None,
    service: Optional[Resource] = None,
    search_query: Optional[str] = None,
) -> str:
    with requests.Session() as sess:
        if news_source_configuration:
            session_doc = _search_sessions_db_for_cookies(
                doc_ref, news_source_configuration.firestore_session_id.value
            )
            if session_doc.to_dict():
                cookies = session_doc.to_dict().get(SESSION_COOKIES_KEY)
                sess.cookies.update(pickle.loads(cookies))
            else:
                news_source_configuration.message_parser_for_login_flow.value(
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
    general_authenticator = partial(
        authentication_and_parse_flow, news_source_configuration=None
    )


def parse_article_url_for_correct_login_flow(
    article_url: str,
) -> Tuple[Callable, Union[Type[ft_enum], Type[substack_enum], None]]:
    if "ft.com" in article_url:
        return SiteAuthenticator.ft_authenticator.value, ft_enum
    if "substack.com" in article_url:
        return SiteAuthenticator.substack_authenticator.value, substack_enum
    if "wsj.com" in article_url:
        raise NotImplementedError
    if "foreignaffairs.com" in article_url:
        raise NotImplementedError
    else:
        return SiteAuthenticator.general_authenticator.value, None
