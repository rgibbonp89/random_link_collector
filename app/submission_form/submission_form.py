"""Starting point for app submission form"""
import streamlit as st


def create_text_submission_form() -> None:
    with st.form("my_form"):
        st.write("Save new article")
        url_input = st.text_input("Article URL")
        name_input = st.text_input("Article name")
        submitted = st.form_submit_button("Submit")
        if submitted:
            st.write("URL: ", url_input)
            st.write("Name: ", name_input)
            st.write("Chat-GPT Summary: ", "Some random text about the article for now")
            st.text_input("My notes")
            final_submission = st.form_submit_button("Final submission")
