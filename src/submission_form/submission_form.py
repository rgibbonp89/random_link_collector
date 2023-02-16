"""Starting point for app submission form"""
import streamlit as st

with st.form("my_form") as form:
    st.write("Inside the form")
    slider_val = st.text_input("Article URL")

    submitted = st.form_submit_button("Submit")
    if submitted:
        st.write("URL: ", slider_val)
        st.write("Chat-GPT Summary: ", "Some random text about the article for now")
        slider_val = st.text_input("Anything else to add?")
