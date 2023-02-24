from __future__ import print_function

from integrations.authenticate import authenticate_user_and_provide_gmail_service
from integrations.logins.news_login import authenticate_news_site
from submission_form.submission_form import create_text_submission_form
import streamlit as st


service = authenticate_user_and_provide_gmail_service()

authenticate_news_site(service)

st.set_page_config(
    page_title="Submit article",
)

st.write("# Welcome to the article saver!")

create_text_submission_form(service)
