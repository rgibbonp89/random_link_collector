"""Starting point for app submission form"""
import asyncio
import json
from typing import Dict, List

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
from flask import request
from backend.integrations.logins.news_login import (
    authenticate_news_site_and_return_cleaned_content,
)

load_dotenv()


db: Client = firestore.Client.from_service_account_json(
    f"{Path(__file__).parent.parent.parent}/.keys/firebase.json"
)

openai.api_key = os.environ.get("OPENAI_KEY")


# Set up the model and prompt
MODEL_ENGINE = "gpt-3.5-turbo"
MAX_TOKENS = 500
TEMPERATURE = 0.01
ID_LENGTH = 15
ARTICLE_COLLECTION = "articles"

NAME_INPUT_KEY = "name_input"
URL_INPUT_KEY = "url_input"
MY_SUMMARY_KEY = "my_summary"
AUTOSUMMARY_PROMPT_KEY = "autosummary_prompt"

expected_keys: List[str] = [
    NAME_INPUT_KEY,
    URL_INPUT_KEY,
    MY_SUMMARY_KEY,
    AUTOSUMMARY_PROMPT_KEY,
]


def _validate_request_contents(request: Dict[str, str]):
    assert list(set(expected_keys) - set(request.keys())) == {}


def create_text_submission_form(service) -> None:
    request_dict: Dict[str, str] = json.loads(request.data.decode("utf-8"))
    _validate_request_contents(request_dict)
    formatted_text = authenticate_news_site_and_return_cleaned_content(
        service, article_url=request_dict.get(URL_INPUT_KEY)
    )
    prompt = (
        f"What are the main arguments in this text: {formatted_text}? "
        f"Please provide your answer in bullet points in markdown."
        if not request_dict.get(AUTOSUMMARY_PROMPT_KEY)
        else request_dict.get(AUTOSUMMARY_PROMPT_KEY)
    )
    request_dict.update({AUTOSUMMARY_PROMPT_KEY: prompt})

    doc_id = add_synchronous_components_to_db(
        db=db,
        collection_name=ARTICLE_COLLECTION,
        **request_dict,
    )

    try:
        completion: Completion = openai.ChatCompletion.create(
            model=MODEL_ENGINE,
            messages=[{"role": "user", "content": prompt}],
            n=1,
            max_tokens=MAX_TOKENS,
            temperature=TEMPERATURE,
        )
        saved_text = (
            completion.choices[0]
            .message.content.replace("• ", "* ")
            .replace("- ", "* ")
        )
    except openai.error.InvalidRequestError as exception:
        saved_text = exception.user_message

    asyncio.run(
        add_async_components_to_db(
            db,
            "articles",
            doc_id,
            saved_text,
            cleaned_text=formatted_text,
        )
    )


def add_synchronous_components_to_db(
    db: Client,
    collection_name: str,
    name_input: str,
    url_input: str,
    my_summary: str,
    prompt: str,
) -> str:
    doc_id = create_doc_id()
    doc_ref = db.collection(collection_name).document(doc_id)
    doc_ref.set(
        {
            "Name": name_input,
            "URL": url_input,
            "MySummary": my_summary,
            "Prompt": prompt,
        }
    )
    return doc_id


async def add_async_components_to_db(
    db: Client,
    collection_name: str,
    doc_id: str,
    chat_gpt_response: str,
    cleaned_text: str,
) -> None:
    doc_ref: DocumentReference = db.collection(collection_name).document(doc_id)
    doc_ref.update(
        {
            "AutoSummary": chat_gpt_response,
            "CleanedText": cleaned_text,
        }
    )


def create_doc_id() -> str:
    return "".join(
        random.choice(string.ascii_uppercase + string.ascii_lowercase)
        for _ in range(ID_LENGTH)
    )
