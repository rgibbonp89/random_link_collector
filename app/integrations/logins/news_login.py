from datetime import date, timedelta

from integrations.logins.login_configs import parse_article_url_for_correct_login_flow


def authenticate_news_site_and_return_cleaned_content(service, article_url) -> str:
    today = date.today()
    window = today - timedelta(days=1)
    _cleaner_fn, news_source_configuration = parse_article_url_for_correct_login_flow(
        article_url
    )
    search_query = None
    if news_source_configuration:
        search_query = news_source_configuration.search_query_gmail.value.format(
            query=window
        )
    return _cleaner_fn(
        service=service, article_url=article_url, search_query=search_query
    )
