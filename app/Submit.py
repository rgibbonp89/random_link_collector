from submission_form.submission_form import create_text_submission_form
import streamlit as st

st.set_page_config(
    page_title="Submit article",
)

st.write("# Welcome to the article saver!")

create_text_submission_form()
