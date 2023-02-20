from submission_form.submission_form import create_text_submission_form
import streamlit as st

## authentication
## https://cloud.google.com/appengine/docs/standard/python3/building-app/authenticating-users
## tech for the initial chatgpt submission - how do i make this async wrt to UI

st.set_page_config(
    page_title="Submit article",
)


st.write("# Welcome to the article saver!")

create_text_submission_form()
