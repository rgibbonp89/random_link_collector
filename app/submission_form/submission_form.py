"""Starting point for app submission form"""
import streamlit as st
from google.cloud import firestore
import os
import string
import random


db = firestore.Client.from_service_account_json(os.environ.get("FS_KEY"))


def create_text_submission_form() -> None:
    with st.form("my_form"):
        st.write("Save new article")
        url_input = st.text_input("Article URL")
        name_input = st.text_input("Article name")
        my_notes = st.text_area("My notes")
        submitted = st.form_submit_button("Submit")

        if submitted:
            # Once the user has submitted, upload it to the database
            st.write("URL: ", url_input)
            st.write("Name: ", name_input)
            doc_ref = db.collection("articles").document(
                "".join(random.choice(string.ascii_uppercase) for _ in range(15))
            )
            doc_ref.set({"Name": name_input, "AutoSummary": my_notes, "URL": url_input})
