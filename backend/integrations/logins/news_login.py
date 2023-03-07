import pickle
import re
from datetime import date, timedelta

from typing import Type, Optional, Union

import requests
from googleapiclient.discovery import Resource
from readability import Document

from backend.integrations.logins.config_enums import (
    parse_article_url_for_correct_login_flow,
)
from backend.integrations.logins.login_configs.base_login_config import SiteConfig
from backend.integrations.logins.login_configs.utils import (
    _search_sessions_db_for_cookies,
    SESSION_COOKIES_KEY,
    doc_ref,
)


CLEANR = re.compile("<.*?>")


def authentication_and_parse_flow(
    article_url: str,
    service: Resource,
    site_config: Type[SiteConfig] = None,
    window: Optional[date] = None,
) -> str:
    with requests.Session() as sess:
        # only attempt to retrieve the session cookies or create new ones if there's a site config defined
        if site_config:
            config = site_config()
            search_query = config.search_query_gmail.format(query=window)
            session_doc = _search_sessions_db_for_cookies(
                doc_ref, config.firestore_session_id
            )
            if session_doc.to_dict():
                cookies = session_doc.to_dict().get(SESSION_COOKIES_KEY)
                sess.cookies.update(pickle.loads(cookies))
            else:
                config.request_code_for_login_and_create_session(
                    service=service,
                    sess=sess,
                    search_query=search_query,
                    doc_ref=doc_ref,
                )
        article_text = sess.get(article_url)
    return re.sub(CLEANR, "", Document(article_text.text).summary())


def authenticate_news_site_and_return_cleaned_content(service, article_url) -> str:
    today = date.today()
    window = today - timedelta(days=1)
    try:
        config_object: Union[
            Type[SiteConfig], None
        ] = parse_article_url_for_correct_login_flow(article_url)
    except NotImplementedError:
        config_object = None
    return authentication_and_parse_flow(
        article_url=article_url,
        site_config=config_object,
        service=service,
        window=window,
    )
