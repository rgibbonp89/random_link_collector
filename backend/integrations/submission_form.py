"""Starting point for app submission form"""
import asyncio
import json
from typing import Dict, Union
from urllib.parse import urlparse

from google.cloud import firestore
from dotenv import load_dotenv
from google.cloud.firestore_v1.client import Client
from pathlib import Path
from flask import request
from backend.integrations.logins.news_login import (
    authenticate_news_site_and_return_cleaned_content,
)
from backend.integrations.model_endpoint import call_model_endpoint
from backend.integrations.utils.utils import (
    _validate_request_for_initial_submission,
    RENDER_MAPPER,
    FrontendReferences,
    DB,
)
from backend.integrations.utils.utils import (
    add_synchronous_components_to_db,
    add_async_components_to_db,
)

load_dotenv()


db: Client = firestore.Client.from_service_account_json(
    f"{Path(__file__).parent.parent.parent}/.keys/firebase.json"
)


def _submit_article(service) -> None:
    request_dict: Dict[str, str] = json.loads(request.data.decode("utf-8"))
    _validate_request_for_initial_submission(request_dict)
    formatted_text: Union[
        str, None
    ] = authenticate_news_site_and_return_cleaned_content(
        service, article_url=request_dict.get(FrontendReferences.URL_INPUT_KEY)
    )
    if formatted_text:
        prompt = (
            f"Can you provide a TL;DR of the following text: {formatted_text}? "
            f"Please provide your answer in bullet points in markdown."
            if not request_dict.get(FrontendReferences.AUTOSUMMARY_PROMPT_KEY)
            else request_dict.get(FrontendReferences.AUTOSUMMARY_PROMPT_KEY)
        )
    else:
        prompt = f"""Just return the following article title (this is pass-through logic in an app):
        {request_dict.get(FrontendReferences.NAME_INPUT_KEY)}"""

    # clean this up and make it generic (update_request fn)
    request_dict.update({FrontendReferences.AUTOSUMMARY_PROMPT_KEY: prompt})
    request_dict.update(
        {
            FrontendReferences.SITE_LABEL_KEY: urlparse(
                request_dict.get(FrontendReferences.URL_INPUT_KEY)
            ).netloc,
            FrontendReferences.READ_STATUS_KEY: False,
        }
    )

    db_insert_dict = {
        RENDER_MAPPER.get(key)[0]: value
        for key, value in request_dict.items()
        if key in list(RENDER_MAPPER.keys())
    }

    doc_id = add_synchronous_components_to_db(
        db=db,
        collection_name=DB.ARTICLES_COLLECTION,
        db_insert_dict=db_insert_dict,
    )

    model_response_text = call_model_endpoint(
        prompt, max_tokens=int(request_dict.get("max_tokens", 500))
    )
    if formatted_text:
        one_liner_prompt = f"Can you summarize this in one line: {model_response_text}?"
        one_liner = call_model_endpoint(
            one_liner_prompt, max_tokens=int(request_dict.get("max_tokens", 500))
        )
    else:
        one_liner = model_response_text

    asyncio.run(
        add_async_components_to_db(
            db,
            DB.ARTICLES_COLLECTION,
            doc_id,
            model_response_text,
            cleaned_text=formatted_text,
            one_liner=one_liner,
        )
    )
