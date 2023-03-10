import asyncio
import json
from typing import Dict, Tuple, Callable, List, Generator, Any
from flask import Blueprint, request, Request
from flask_cors import CORS
from google.cloud.firestore_v1 import (
    DocumentSnapshot,
)
from fuzzywuzzy import fuzz
from backend.integrations.model_enpoint import call_model_endpoint
from backend.integrations.utils.utils import (
    add_async_components_to_db,
    add_synchronous_components_to_db,
    _validate_request_for_update_article,
    _validate_request_for_update_article_sync_db,
    MY_SUMMARY_KEY,
    AUTOSUMMARY_KEY,
    NAME_INPUT_KEY,
    URL_INPUT_KEY,
    AUTOSUMMARY_PROMPT_KEY,
    SHORT_SUMMARY_KEY,
    COLLECTION_NAME,
    SITE_LABEL_KEY,
    _make_db_connection,
)

articles_blue = Blueprint("articlesblue", __name__)
CORS(articles_blue)

SEARCH_STRICTNESS_CONSTANT = 95
SEARCH_STRICTNESS_KEY = "search_strictness"
UPDATE_AUTO_SUMMARY_KEY = "update_auto_summary"
DOCUMENT_NAME_KEY = "Name"

RENDER_MAPPER: Dict[str, Tuple[str, Callable]] = {
    MY_SUMMARY_KEY: ("MySummary", lambda x: x),
    AUTOSUMMARY_KEY: (
        "AutoSummary",
        lambda x: x.replace("• ", "* ")
        .replace("- ", "* ")
        .replace("Main arguments:", ""),
    ),
    NAME_INPUT_KEY: ("Name", lambda x: x),
    URL_INPUT_KEY: ("URL", lambda x: x),
    SHORT_SUMMARY_KEY: ("ShortSummary", lambda x: x),
    SITE_LABEL_KEY: ("SiteLabel", lambda x: x),
}


def _view_record(record: DocumentSnapshot) -> Dict[str, str]:
    out = {}
    dict_record = record.to_dict()
    for rendered_name, db_field_and_render_fn in RENDER_MAPPER.items():
        out.update(
            {
                f"{rendered_name}": db_field_and_render_fn[1](
                    dict_record.get(db_field_and_render_fn[0], "")
                ),
            }
        )
    return out


def _view_all_records() -> List[Dict[str, str]]:
    output_list = list()
    _, _, _, list_in_first_tab = _make_db_connection()
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
    db, doc_ref, docs, list_in_first_tab = _make_db_connection()
    result_docs: Generator[DocumentSnapshot, Any, None] = doc_ref.stream()
    return [
        r_doc
        for r_doc in result_docs
        if fuzz.token_sort_ratio(
            r_doc.to_dict().get(RENDER_MAPPER.get(NAME_INPUT_KEY)[0]),
            request_dict.get(NAME_INPUT_KEY),
        )
        > search_strictness
    ]


@articles_blue.route("/getallarticles", endpoint="getallarticles", methods=["GET"])
def get_all_articles():
    return _view_all_records()


@articles_blue.route("/getsinglearticle", endpoint="getsinglearticle", methods=["POST"])
def get_single_article():
    _, doc_ref, _, _ = _make_db_connection()
    doc_id, _, _ = _match_record_and_find_id(request_obj=request)
    return _view_record(doc_ref.document(doc_id).get())


@articles_blue.route(
    "/deletesinglearticle", endpoint="deletesinglearticle", methods=["POST"]
)
def delete_single_article():
    _, doc_ref, _, _ = _make_db_connection()
    doc_id, _, _ = _match_record_and_find_id(request_obj=request)
    doc_ref.document(doc_id).delete()
    return json.dumps({"success": True}), 200, {"ContentType": "application/json"}


@articles_blue.route("/updatearticle", endpoint="updatearticle", methods=["POST"])
def update_article():
    db, doc_ref, _, _ = _make_db_connection()

    doc_id, number_results_found, request_dict = _match_record_and_find_id(
        request_obj=request
    )
    _validate_request_for_update_article(request=request_dict)
    request_dict.update({"doc_id": doc_id})
    doc: Dict[str, str] = doc_ref.document(doc_id).get().to_dict()
    cleaned_text, prompt = doc.get("CleanedText"), doc.get("Prompt")
    if request_dict.get(UPDATE_AUTO_SUMMARY_KEY) == "true":
        model_response_text: str = call_model_endpoint(prompt)
        one_liner_prompt = (
            f"Can you summarize this in one sentence: {model_response_text}?"
        )
        one_liner = call_model_endpoint(one_liner_prompt)
        asyncio.run(
            add_async_components_to_db(
                db,
                COLLECTION_NAME,
                doc_id,
                model_response_text,
                cleaned_text=cleaned_text,
                one_liner=one_liner,
            )
        )
    request_dict.pop(UPDATE_AUTO_SUMMARY_KEY, None)
    request_dict.pop(SEARCH_STRICTNESS_KEY, None)
    request_dict.update({URL_INPUT_KEY: doc.get("URL"), AUTOSUMMARY_PROMPT_KEY: prompt})
    _validate_request_for_update_article_sync_db(request=request_dict)
    add_synchronous_components_to_db(db, COLLECTION_NAME, **request_dict)
    return json.dumps({"success": True}), 200, {"ContentType": "application/json"}
