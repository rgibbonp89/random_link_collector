import random
import string
from functools import partial
from pathlib import Path
from typing import List, Optional, Dict, Generator, Tuple, Callable

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
READ_STATUS_KEY = "read_status"
ID_LIST_KEY = "id_list"
NAME_LIST_KEY = "name_list"
SYNTHESIS_KEY = "synthesis"
URL_LIST_KEY = "url_list"
SYNTHESIS_TITLE_KEY = "synthesis_title"
EXPLAINED_CONTENT_KEY = "explained_content"
DAILY_NOTE_TEXT_KEY = "daily_note_text"
DATE_INPUT_KEY = "date_input"

NAME_INPUT_KEY_DB = "Name"
URL_INPUT_KEY_DB = "URL"
MY_SUMMARY_KEY_DB = "MySummary"
AUTOSUMMARY_PROMPT_KEY_DB = "Prompt"
AUTOSUMMARY_KEY_DB = "AutoSummary"
SHORT_SUMMARY_KEY_DB = "ShortSummary"
SITE_LABEL_KEY_DB = "SiteLabel"
READ_STATUS_KEY_DB = "ReadStatus"
ELI5_KEY_DB = "ELI5"
CLEANED_TEXT_KEY_DB = "CleanedText"
ID_LIST_KEY_DB = "IDList"
SYNTHESIS_KEY_DB = "Synthesis"
URL_LIST_KEY_DB = "URLList"
NAME_LIST_KEY_DB = "NameList"
SYNTHESIS_TITLE_KEY_DB = "SynthesisTitle"
EXPLAINED_CONTENT_KEY_DB = "ExplainedContent"
DAILY_NOTE_TEXT_KEY_DB = "DailyNoteText"
DATE_INPUT_KEY_DB = "DateInput"

ARTICLES_COLLECTION = "articles"
SYNTHESIS_COLLECTION = "syntheses"
DAILY_NOTES_COLLECTION = "notes"


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

RENDER_MAPPER: Dict[str, Tuple[str, Callable]] = {
    MY_SUMMARY_KEY: (MY_SUMMARY_KEY_DB, lambda x: x),
    AUTOSUMMARY_KEY: (
        AUTOSUMMARY_KEY_DB,
        lambda x: x.replace("• ", "* ")
        .replace("- ", "* ")
        .replace("Main arguments:", ""),
    ),
    NAME_INPUT_KEY: (NAME_INPUT_KEY_DB, lambda x: x),
    URL_INPUT_KEY: (URL_INPUT_KEY_DB, lambda x: x),
    SHORT_SUMMARY_KEY: (SHORT_SUMMARY_KEY_DB, lambda x: x),
    SITE_LABEL_KEY: (SITE_LABEL_KEY_DB, lambda x: x),
    READ_STATUS_KEY: (READ_STATUS_KEY_DB, lambda x: x),
    EXPLAINED_CONTENT_KEY: (EXPLAINED_CONTENT_KEY_DB, lambda x: x),
}


SYNTHESIS_RENDER_MAPPER: Dict[str, Tuple[str, Callable]] = {
    SYNTHESIS_TITLE_KEY: (SYNTHESIS_TITLE_KEY_DB, lambda x: x),
    NAME_LIST_KEY: (NAME_LIST_KEY_DB, lambda x: x),
    SYNTHESIS_KEY: (SYNTHESIS_KEY_DB, lambda x: x),
    URL_LIST_KEY: (URL_LIST_KEY_DB, lambda x: x),
}

DAILY_NOTE_RENDER_MAPPER: Dict[str, Tuple[str, Callable]] = {
    DAILY_NOTE_TEXT_KEY: (DAILY_NOTE_TEXT_KEY_DB, lambda x: x),
    DATE_INPUT_KEY: (DATE_INPUT_KEY_DB, lambda x: x),
}


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
    db_insert_dict: Dict[str, str],
    doc_id: Optional[str] = None,
) -> str:
    reference_exists = True if doc_id else False
    if not reference_exists:
        doc_id = create_doc_id()
    doc_ref = db.collection(collection_name).document(doc_id)
    if not reference_exists:
        doc_ref.set(db_insert_dict)
    else:
        doc_ref.update(db_insert_dict)
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
            AUTOSUMMARY_KEY_DB: chat_gpt_response,
            CLEANED_TEXT_KEY_DB: cleaned_text,
            SHORT_SUMMARY_KEY_DB: one_liner,
        }
    )


def _make_db_connection(collection_name: str = ARTICLES_COLLECTION):
    db: Client = firestore.Client.from_service_account_json(
        f"{Path(__file__).parent.parent.parent.parent}/.keys/firebase.json"
    )
    doc_ref: CollectionReference = db.collection(collection_name)
    docs: Generator[DocumentSnapshot] = doc_ref.stream()
    list_in_first_tab: List[DocumentSnapshot] = sorted(
        [doc for doc in docs], key=lambda x: x.create_time, reverse=True
    )
    return db, doc_ref, docs, list_in_first_tab
