"""Starting point for app submission form"""
import asyncio
import json
from typing import Dict

from google.cloud import firestore
from dotenv import load_dotenv
from google.cloud.firestore_v1.client import Client
from pathlib import Path
from flask import request
from backend.integrations.logins.news_login import (
    authenticate_news_site_and_return_cleaned_content,
)
from backend.integrations.model_enpoint import call_model_endpoint
from backend.integrations.utils.utils import (
    URL_INPUT_KEY,
    AUTOSUMMARY_PROMPT_KEY,
    _validate_request_for_initial_submission,
)
from backend.integrations.utils.utils import (
    add_synchronous_components_to_db,
    add_async_components_to_db,
)

load_dotenv()


db: Client = firestore.Client.from_service_account_json(
    f"{Path(__file__).parent.parent.parent}/.keys/firebase.json"
)

ARTICLE_COLLECTION = "articles"


def _submit_article(service) -> None:
    request_dict: Dict[str, str] = json.loads(request.data.decode("utf-8"))
    _validate_request_for_initial_submission(request_dict)
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

    model_response_text = call_model_endpoint(prompt)
    one_liner_prompt = f"Can you summarize this in one line: {model_response_text}?"
    one_liner = call_model_endpoint(one_liner_prompt)

    asyncio.run(
        add_async_components_to_db(
            db,
            "articles",
            doc_id,
            model_response_text,
            cleaned_text=formatted_text,
            one_liner=one_liner,
        )
    )
