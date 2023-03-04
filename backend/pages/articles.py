import asyncio
import json
from typing import Dict, Tuple, Callable, List, Generator, Any
from flask import Blueprint, request, Request
import streamlit as st
from google.cloud import firestore
from google.cloud.firestore_v1 import (
    Client,
    CollectionReference,
    DocumentSnapshot,
)
from pathlib import Path
from fuzzywuzzy import fuzz
from backend.integrations.model_enpoint import call_model_endpoint
from backend.integrations.async_db_write import add_async_components_to_db

articles_blue = Blueprint("articlesblue", __name__)


SEARCH_STRICTNESS_CONSTANT = 95
SEARCH_STRICTNESS_KEY = "search_strictness"
UPDATE_AUTO_SUMMARY_KEY = "update_auto_summary"
DOCUMENT_NAME_KEY = "Name"

db: Client = firestore.Client.from_service_account_json(
    f"{Path(__file__).parent.parent.parent}/.keys/firebase.json"
)
doc_ref: CollectionReference = db.collection("articles")

docs = doc_ref.stream()

list_in_first_tab = sorted(
    [doc for doc in docs], key=lambda x: x.create_time, reverse=True
)


RENDER_MAPPER: Dict[str, Tuple[str, Callable]] = {
    "My summary": ("MySummary", lambda x: x),
    "Auto-summary": (
        "AutoSummary",
        lambda x: x.replace("• ", "* ").replace("- ", "* "),
    ),
    "Name": ("Name", lambda x: x),
    "URL": ("URL", lambda x: x),
}


def _view_record(record):
    out = {}
    for rendered_name, db_field_and_render_fn in RENDER_MAPPER.items():
        out.update(
            {
                f"{rendered_name}": db_field_and_render_fn[1](
                    record.to_dict()[db_field_and_render_fn[0]]
                ),
            }
        )
    return out


def _view_all_records() -> List[Dict[str, str]]:
    output_list = list()
    for record in list_in_first_tab:
        output_list.append(_view_record(record))
    return output_list


def _match_record_and_find_id(request_obj: Request):
    request_dict: Dict[str, str] = json.loads(request_obj.data.decode("utf-8"))
    search_strictness = int(
        request_dict.get(SEARCH_STRICTNESS_KEY, SEARCH_STRICTNESS_CONSTANT)
    )
    result_docs_pruned = _match_entries(request_dict, search_strictness)
    number_results_found: int = len(result_docs_pruned)
    assert number_results_found == 1
    doc_id = result_docs_pruned[0].id
    return doc_id, number_results_found, request_dict


def _match_entries(request_dict, search_strictness):
    result_docs: Generator[DocumentSnapshot, Any, None] = doc_ref.stream()
    return [
        r_doc
        for r_doc in result_docs
        if fuzz.token_sort_ratio(
            r_doc.to_dict().get(DOCUMENT_NAME_KEY), request_dict.get(DOCUMENT_NAME_KEY)
        )
        > search_strictness
    ]


@articles_blue.route("/getallarticles", endpoint="getallarticles", methods=["GET"])
def get_all_articles():
    return _view_all_records()


@articles_blue.route("/getsinglearticle", endpoint="getsinglearticle", methods=["POST"])
def get_single_article():
    doc_id, _, _ = _match_record_and_find_id(request_obj=request)
    return doc_ref.document(doc_id).get().to_dict()


@articles_blue.route(
    "/deletesinglearticle", endpoint="deletesinglearticle", methods=["POST"]
)
def delete_single_article():
    doc_id, _, _ = _match_record_and_find_id(request_obj=request)
    doc_ref.document(doc_id).delete()
    return json.dumps({"success": True}), 200, {"ContentType": "application/json"}


@articles_blue.route("/updatearticle", endpoint="updatearticle", methods=["POST"])
def update_article():
    doc_id, number_results_found, request_dict = _match_record_and_find_id(
        request_obj=request
    )
    if request_dict.get(UPDATE_AUTO_SUMMARY_KEY) == "true":
        doc: Dict[str, str] = doc_ref.document(doc_id).get().to_dict()
        cleaned_text, prompt = doc.get("CleanedText"), doc.get("Prompt")

        saved_text: str = call_model_endpoint(prompt)
        asyncio.run(
            add_async_components_to_db(
                db,
                "articles",
                doc_id,
                saved_text,
                cleaned_text=cleaned_text,
            )
        )
        request_dict.pop(UPDATE_AUTO_SUMMARY_KEY, None)
    request_dict.pop(SEARCH_STRICTNESS_KEY, None)
    ## I need to validate the keys that can be updated here
    doc_ref.document(doc_id).update(request_dict)
    return json.dumps({"success": True}), 200, {"ContentType": "application/json"}
