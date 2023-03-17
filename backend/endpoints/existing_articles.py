import asyncio
import json
from typing import Dict, List, Generator, Any, Optional
from flask import Blueprint, request, Request
from flask_cors import CORS
from google.cloud.firestore_v1 import (
    DocumentSnapshot,
    DocumentReference,
)
from fuzzywuzzy import fuzz
from backend.integrations.model_enpoint import call_model_endpoint
from backend.integrations.utils.utils import (
    add_synchronous_components_to_db,
    NAME_INPUT_KEY,
    COLLECTION_NAME,
    _make_db_connection,
    SYNTHESIS_COLLECTION,
    create_doc_id,
    ID_LIST_KEY_DB,
    SYNTHESIS_KEY_DB,
    URL_LIST_KEY_DB,
)
from backend.integrations.utils.utils import RENDER_MAPPER

articles_blue = Blueprint("articlesblue", __name__)
CORS(articles_blue)

SEARCH_STRICTNESS_CONSTANT = 95
SEARCH_STRICTNESS_KEY = "search_strictness"
UPDATE_AUTO_SUMMARY_KEY = "update_auto_summary"
DOCUMENT_NAME_KEY = "Name"


def _view_record(record: DocumentSnapshot) -> Dict[str, str]:
    out = {}
    dict_record = record.to_dict()
    for rendered_name, db_field_and_render_fn in RENDER_MAPPER.items():
        out.update(
            {
                f"{rendered_name}": db_field_and_render_fn[1](
                    dict_record.get(db_field_and_render_fn[0], "")
                ),
            },
            **{"id": record.id},
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


@articles_blue.route("/deletearticle", endpoint="deletearticle", methods=["POST"])
def delete_single_article():
    request_dict: Dict[str, str] = json.loads(request.data.decode("utf-8"))
    _, doc_ref, _, _ = _make_db_connection()
    doc_id = request_dict.get("id")
    doc_ref.document(doc_id).delete()
    return json.dumps({"success": True}), 200, {"ContentType": "application/json"}


@articles_blue.route("/update_article", endpoint="/update_article", methods=["POST"])
def update_article_flow():
    request_dict: Dict[str, str] = json.loads(request.data.decode("utf-8"))
    db, doc_ref, _, _ = _make_db_connection()
    doc_id = request_dict.get("id")
    request_dict.pop("id")
    db_insert_dict = {
        RENDER_MAPPER.get(key)[0]: value for key, value in request_dict.items()
    }
    add_synchronous_components_to_db(
        db, COLLECTION_NAME, doc_id=doc_id, db_insert_dict=db_insert_dict
    )
    return request_dict


@articles_blue.route("/getreadstatus", endpoint="/getreadstatus", methods=["POST"])
def get_read_status():
    request_dict: Dict[str, str] = json.loads(request.data.decode("utf-8"))
    db, doc_ref, _, _ = _make_db_connection()
    doc: DocumentReference = doc_ref.document(request_dict.get("id"))
    return {"read_status": doc.get().to_dict().get("ReadStatus")}


@articles_blue.route("/createsynthesis", endpoint="/createsynthesis", methods=["POST"])
def create_synthesis():
    request_dict: Dict[str, str] = json.loads(request.data.decode("utf-8"))
    ids: Optional[List[str], None] = request_dict.get("ids")
    topic: str = request_dict.get("topic")
    db, doc_ref, _, _ = _make_db_connection()
    out_content: Dict[str, List[str, str]] = dict()
    for id in ids:
        out_content.update(
            {
                id: [
                    doc_ref.document(id).get().to_dict().get("AutoSummary"),
                    doc_ref.document(id).get().to_dict().get("URL"),
                ]
            }
        )

    synthesis_prompt = f"""Provide a synthesis of the following {len(ids)} texts.
    Focus on where they agree and differ, providing an overview of where
    their authors stand on the topic of {topic}: \n"""
    i = 1
    for id, text in out_content.items():
        synthesis_prompt += f" \n Article {i}: {text[0]}"
        i += 1

    model_synthesis = call_model_endpoint(synthesis_prompt)
    doc_id = create_doc_id()
    doc_ref = db.collection(SYNTHESIS_COLLECTION).document(doc_id)
    doc_ref.set(
        {
            ID_LIST_KEY_DB: ids,
            SYNTHESIS_KEY_DB: model_synthesis,
            URL_LIST_KEY_DB: [value[1] for keys, value in out_content.items()],
        }
    )
    return json.dumps({"success": True}), 200, {"ContentType": "application/json"}
