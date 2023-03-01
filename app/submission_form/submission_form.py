"""Starting point for app submission form"""
import asyncio

import streamlit as st
from google.cloud import firestore
import os
import string
import random
import openai
from dotenv import load_dotenv
from google.cloud.firestore_v1 import DocumentReference
from google.cloud.firestore_v1.client import Client
from openai import Completion
from pathlib import Path

from integrations.logins.news_login import (
    authenticate_news_site_and_return_cleaned_content,
)

load_dotenv()


db: Client = firestore.Client.from_service_account_json(
    f"{Path(__file__).parent.parent.parent}/.keys/firebase.json"
)

openai.api_key = os.environ.get("OPENAI_KEY")


# Set up the model and prompt
MODEL_ENGINE = "text-davinci-003"
MAX_TOKENS = 500
TEMPERATURE = 0.01
ID_LENGTH = 15
ARTICLE_COLLECTION = "articles"


def create_text_submission_form(service) -> None:
    with st.form("my_form"):
        st.write("Save new article")
        url_input = st.text_input("Article URL")
        name_input = st.text_input("Article name")
        my_summary = st.text_area("My summary")
        autosummary_prompt = st.text_area("Auto-summary prompt")
        submitted = st.form_submit_button("Submit")

        if submitted:
            st.write("**URL:**", url_input)
            st.write("**Name:**", name_input)
            st.text_area("**My summary:**", my_summary)
            doc_id = add_synchronous_components_to_db(
                db=db,
                collection_name=ARTICLE_COLLECTION,
                name_input=name_input,
                url_input=url_input,
                my_summary=my_summary,
            )
            formatted_text = authenticate_news_site_and_return_cleaned_content(
                service, article_url=url_input
            )
            prompt = (
                f"What are the main arguments in this text: {formatted_text}? "
                f"Please provide your answer in bullet points in markdown."
                if not autosummary_prompt
                else autosummary_prompt
            )
            try:
                completion: Completion = openai.Completion.create(
                    engine=MODEL_ENGINE,
                    prompt=prompt,
                    n=1,
                    max_tokens=MAX_TOKENS,
                    temperature=TEMPERATURE,
                )
                saved_text = (
                    completion.choices[0].text.replace("•", "*").replace("-", "*")
                )
            except openai.error.InvalidRequestError as exception:
                saved_text = exception.user_message
            asyncio.run(
                add_async_components_to_db(
                    db,
                    "articles",
                    doc_id,
                    saved_text,
                    prompt=prompt,
                    cleaned_text=formatted_text,
                )
            )


def add_synchronous_components_to_db(
    db: Client,
    collection_name: str,
    name_input: str,
    url_input: str,
    my_summary: str,
) -> str:
    doc_id = create_doc_id()
    doc_ref = db.collection(collection_name).document(doc_id)
    doc_ref.set(
        {
            "Name": name_input,
            "URL": url_input,
            "MySummary": my_summary,
        }
    )
    return doc_id


async def add_async_components_to_db(
    db: Client,
    collection_name: str,
    doc_id: str,
    chat_gpt_response: str,
    prompt: str,
    cleaned_text: str,
) -> None:
    doc_ref: DocumentReference = db.collection(collection_name).document(doc_id)
    doc_ref.update(
        {
            "AutoSummary": chat_gpt_response,
            "Prompt": prompt,
            "CleanedText": cleaned_text,
        }
    )


def create_doc_id() -> str:
    return "".join(
        random.choice(string.ascii_uppercase + string.ascii_lowercase)
        for _ in range(ID_LENGTH)
    )
