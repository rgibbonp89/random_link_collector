from enum import Enum
from typing import Type, Union
from integrations.logins.login_configs.base_login_config import SiteConfig
from integrations.logins.login_configs.news_login_configs import (
    FTLoginConfig,
    SubstackLoginConfig,
    ForeignAffairsLoginConfig,
)


class SiteAuthenticator(Enum):
    ft_authenticator = FTLoginConfig
    substack_authenticator = SubstackLoginConfig
    foreign_affairs_authenticator = ForeignAffairsLoginConfig
    general_authenticator = None


def parse_article_url_for_correct_login_flow(
    article_url: str,
) -> Union[Type[SiteConfig], None]:
    if "ft.com" in article_url:
        return SiteAuthenticator.ft_authenticator.value
    if "substack.com" in article_url:
        return SiteAuthenticator.substack_authenticator.value
    if "wsj.com" in article_url:
        raise NotImplementedError
    if "foreignaffairs.com" in article_url:
        return SiteAuthenticator.foreign_affairs_authenticator.value
    else:
        return SiteAuthenticator.general_authenticator.value
