import random
import string
from enum import Enum
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


class FrontendReferences(str, Enum):
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


class DBReferences(str, Enum):
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


class DB(str, Enum):
    ARTICLES_COLLECTION = "articles"
    SYNTHESIS_COLLECTION = "syntheses"
    DAILY_NOTES_COLLECTION = "notes"


class ContentHandler(str, Enum):
    LENGTH_TOO_LONG = "This model's maximum context length"


expected_keys_initial_submission: List[str] = [
    FrontendReferences.NAME_INPUT_KEY,
    FrontendReferences.URL_INPUT_KEY,
    FrontendReferences.MY_SUMMARY_KEY,
]
expected_keys_edit_article: List[str] = [
    FrontendReferences.NAME_INPUT_KEY,
]
expected_keys_edit_article_sync_db: List[str] = [
    FrontendReferences.NAME_INPUT_KEY,
    FrontendReferences.URL_INPUT_KEY,
    FrontendReferences.MY_SUMMARY_KEY,
    FrontendReferences.AUTOSUMMARY_PROMPT_KEY,
]

RENDER_MAPPER: Dict[str, Tuple[str, Callable]] = {
    FrontendReferences.MY_SUMMARY_KEY: (DBReferences.MY_SUMMARY_KEY_DB, lambda x: x),
    FrontendReferences.AUTOSUMMARY_KEY: (
        DBReferences.AUTOSUMMARY_KEY_DB,
        lambda x: x.replace("• ", "* ")
        .replace("- ", "* ")
        .replace("Main arguments:", ""),
    ),
    FrontendReferences.NAME_INPUT_KEY: (DBReferences.NAME_INPUT_KEY_DB, lambda x: x),
    FrontendReferences.URL_INPUT_KEY: (DBReferences.URL_INPUT_KEY_DB, lambda x: x),
    FrontendReferences.SHORT_SUMMARY_KEY: (
        DBReferences.SHORT_SUMMARY_KEY_DB,
        lambda x: x,
    ),
    FrontendReferences.SITE_LABEL_KEY: (DBReferences.SITE_LABEL_KEY_DB, lambda x: x),
    FrontendReferences.READ_STATUS_KEY: (DBReferences.READ_STATUS_KEY_DB, lambda x: x),
    FrontendReferences.EXPLAINED_CONTENT_KEY: (
        DBReferences.EXPLAINED_CONTENT_KEY_DB,
        lambda x: x,
    ),
}


SYNTHESIS_RENDER_MAPPER: Dict[str, Tuple[str, Callable]] = {
    FrontendReferences.SYNTHESIS_TITLE_KEY: (
        DBReferences.SYNTHESIS_TITLE_KEY_DB,
        lambda x: x,
    ),
    FrontendReferences.NAME_LIST_KEY: (DBReferences.NAME_LIST_KEY_DB, lambda x: x),
    FrontendReferences.SYNTHESIS_KEY: (DBReferences.SYNTHESIS_KEY_DB, lambda x: x),
    FrontendReferences.URL_LIST_KEY: (DBReferences.URL_LIST_KEY_DB, lambda x: x),
}

DAILY_NOTE_RENDER_MAPPER: Dict[str, Tuple[str, Callable]] = {
    FrontendReferences.DAILY_NOTE_TEXT_KEY: (
        DBReferences.DAILY_NOTE_TEXT_KEY_DB,
        lambda x: x,
    ),
    FrontendReferences.DATE_INPUT_KEY: (DBReferences.DATE_INPUT_KEY_DB, lambda x: x),
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
            DBReferences.AUTOSUMMARY_KEY_DB: chat_gpt_response,
            DBReferences.CLEANED_TEXT_KEY_DB: cleaned_text,
            DBReferences.SHORT_SUMMARY_KEY_DB: one_liner,
        }
    )


def _make_db_connection(collection_name: str = DB.ARTICLES_COLLECTION):
    db: Client = firestore.Client.from_service_account_json(
        f"{Path(__file__).parent.parent.parent.parent}/.keys/firebase.json"
    )
    doc_ref: CollectionReference = db.collection(collection_name)
    docs: Generator[DocumentSnapshot] = doc_ref.stream()
    list_in_first_tab: List[DocumentSnapshot] = sorted(
        [doc for doc in docs], key=lambda x: x.create_time, reverse=True
    )
    return db, doc_ref, docs, list_in_first_tab
