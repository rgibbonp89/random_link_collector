import random
import string
from functools import partial
from pathlib import Path
from typing import List, Optional, Dict, Generator

from google.cloud import firestore
from google.cloud.firestore_v1 import (
    Client,
    DocumentReference,
    DocumentSnapshot,
    CollectionReference,
)

ID_LENGTH = 15
NAME_INPUT_KEY = "name_input"
URL_INPUT_KEY = "url_input"
MY_SUMMARY_KEY = "my_summary"
AUTOSUMMARY_PROMPT_KEY = "prompt"
AUTOSUMMARY_KEY = "auto_summary"
SHORT_SUMMARY_KEY = "short_summary"
SITE_LABEL_KEY = "site_label"

expected_keys_initial_submission: List[str] = [
    NAME_INPUT_KEY,
    URL_INPUT_KEY,
    MY_SUMMARY_KEY,
]
expected_keys_edit_article: List[str] = [
    NAME_INPUT_KEY,
]
expected_keys_edit_article_sync_db: List[str] = [
    NAME_INPUT_KEY,
    URL_INPUT_KEY,
    MY_SUMMARY_KEY,
    AUTOSUMMARY_PROMPT_KEY,
]


def _validate_request_contents(
    request: Dict[str, str], request_expected_keys: List[str]
):
    missing_keys = set(set(request_expected_keys) - set(list(request.keys())))
    try:
        assert missing_keys == set()
    except AssertionError:
        print(f"Missing {missing_keys}")
        exit(1)


_validate_request_for_initial_submission = partial(
    _validate_request_contents, request_expected_keys=expected_keys_initial_submission
)
_validate_request_for_update_article = partial(
    _validate_request_contents, request_expected_keys=expected_keys_edit_article
)
_validate_request_for_update_article_sync_db = partial(
    _validate_request_contents, request_expected_keys=expected_keys_edit_article_sync_db
)


def add_synchronous_components_to_db(
    db: Client,
    collection_name: str,
    name_input: str,
    url_input: str,
    my_summary: str,
    prompt: str,
    site_label: str,
    doc_id: Optional[str] = None,
) -> str:
    reference_exists = True if doc_id else False
    if not reference_exists:
        doc_id = create_doc_id()
    doc_ref = db.collection(collection_name).document(doc_id)
    if not reference_exists:
        doc_ref.set(
            {
                "Name": name_input,
                "URL": url_input,
                "MySummary": my_summary,
                "Prompt": prompt,
                "SiteLabel": site_label,
            }
        )
    else:
        doc_ref.update(
            {
                "Name": name_input,
                "URL": url_input,
                "MySummary": my_summary,
                "Prompt": prompt,
                "SiteLabel": site_label,
            }
        )
    return doc_id


def create_doc_id() -> str:
    return "".join(
        random.choice(string.ascii_uppercase + string.ascii_lowercase)
        for _ in range(ID_LENGTH)
    )


async def add_async_components_to_db(
    db: Client,
    collection_name: str,
    doc_id: str,
    chat_gpt_response: str,
    cleaned_text: str,
    one_liner: str,
) -> None:
    doc_ref: DocumentReference = db.collection(collection_name).document(doc_id)
    doc_ref.update(
        {
            "AutoSummary": chat_gpt_response,
            "CleanedText": cleaned_text,
            "ShortSummary": one_liner,
        }
    )


COLLECTION_NAME = "articles"


def _make_db_connection():
    db: Client = firestore.Client.from_service_account_json(
        f"{Path(__file__).parent.parent.parent.parent}/.keys/firebase.json"
    )
    doc_ref: CollectionReference = db.collection(COLLECTION_NAME)
    docs: Generator[DocumentSnapshot] = doc_ref.stream()
    list_in_first_tab: List[DocumentSnapshot] = sorted(
        [doc for doc in docs], key=lambda x: x.create_time, reverse=True
    )
    return db, doc_ref, docs, list_in_first_tab
