import pickle
from pathlib import Path
from typing import Union

from google.cloud.firestore_v1 import CollectionReference, DocumentSnapshot
from requests import Session
from google.cloud import firestore
from google.cloud.firestore_v1 import Client

SESSION_COOKIES_KEY = "session_cookies"

db: Client = firestore.Client.from_service_account_json(
    f"{Path(__file__).parent.parent.parent.parent.parent}/.keys/firebase.json"
)
doc_ref = db.collection("sessions")


def _search_sessions_db_for_cookies(
    documents: CollectionReference, document_name: str
) -> Union[DocumentSnapshot, None]:
    return documents.document(document_name).get()


def _save_sessions_cookies_to_db(
    documents: CollectionReference,
    document_name: str,
    session_obj_name: str,
    session_obj: Session,
) -> None:
    pickled_cookies = pickle.dumps(session_obj.cookies)
    documents.document(document_name).set({session_obj_name: pickled_cookies})
