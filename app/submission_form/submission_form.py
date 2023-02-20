"""Starting point for app submission form"""
import streamlit as st
from google.cloud import firestore
import os
import string
import random
import openai
from dotenv import load_dotenv

load_dotenv()

db = firestore.Client.from_service_account_json("./.keys/firebase.json")

openai.api_key = os.environ.get("OPENAI_KEY")

# Set up the model and prompt
MODEL_ENGINE = "text-davinci-003"
MAX_TOKENS = 4000
TEMPERATURE = 0.1
ID_LENGTH = 15


def create_text_submission_form() -> None:
    with st.form("my_form"):
        st.write("Save new article")
        url_input = st.text_input("Article URL")
        name_input = st.text_input("Article name")
        submitted = st.form_submit_button("Submit")

        if submitted:
            # Once the user has submitted, upload it to the database
            st.write("URL: ", url_input)
            st.write("Name: ", name_input)
            # This needs to be made async
            completion = openai.Completion.create(
                engine=MODEL_ENGINE,
                prompt=f"Could you summarize this article {url_input}? You don't have to keep it short.",
                n=1,
                max_tokens=MAX_TOKENS,
                temperature=TEMPERATURE,
            )
            doc_ref = db.collection("articles").document(
                "".join(
                    random.choice(string.ascii_uppercase + string.ascii_lowercase)
                    for _ in range(ID_LENGTH)
                )
            )
            doc_ref.set(
                {
                    "Name": name_input,
                    "AutoSummary": completion.choices[0].text,
                    "URL": url_input,
                }
            )
