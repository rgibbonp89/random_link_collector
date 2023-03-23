import datetime
import logging
import re
import json
from typing import Dict, List, Generator, Any, Optional, Tuple, Callable
from flask import Blueprint, request, Request
from flask_cors import CORS
from google.cloud.firestore_v1 import (
    DocumentSnapshot,
    DocumentReference,
)
from fuzzywuzzy import fuzz
from backend.integrations.model_enpoint import call_model_endpoint, MODEL_ENGINE_LARGE
from backend.integrations.utils.utils import (
    add_synchronous_components_to_db,
    NAME_INPUT_KEY,
    ARTICLES_COLLECTION,
    _make_db_connection,
    SYNTHESIS_COLLECTION,
    create_doc_id,
    ID_LIST_KEY_DB,
    SYNTHESIS_KEY_DB,
    URL_LIST_KEY_DB,
    AUTOSUMMARY_KEY_DB,
    URL_INPUT_KEY_DB,
    NAME_INPUT_KEY_DB,
    NAME_LIST_KEY_DB,
    SYNTHESIS_TITLE_KEY_DB,
    SYNTHESIS_RENDER_MAPPER,
    RENDER_MAPPER,
    EXPLAINED_CONTENT_KEY,
    EXPLAINED_CONTENT_KEY_DB,
    CLEANED_TEXT_KEY_DB,
    DAILY_NOTE_RENDER_MAPPER,
    DAILY_NOTES_COLLECTION,
    DAILY_NOTE_TEXT_KEY,
    DAILY_NOTE_TEXT_KEY_DB,
    DATE_INPUT_KEY_DB,
)

articles_blue = Blueprint("articlesblue", __name__)
CORS(articles_blue)

SEARCH_STRICTNESS_CONSTANT = 95
SEARCH_STRICTNESS_KEY = "search_strictness"
UPDATE_AUTO_SUMMARY_KEY = "update_auto_summary"
DOCUMENT_NAME_KEY = "Name"

logger = logging.getLogger(__name__)


def _view_record(
    record: DocumentSnapshot,
    render_mapper: Optional[Dict[str, Tuple[str, Callable]]] = None,
) -> Dict[str, str]:
    if render_mapper is None:
        render_mapper = RENDER_MAPPER
    out = {}
    dict_record = record.to_dict()
    for rendered_name, db_field_and_render_fn in render_mapper.items():
        out.update(
            {
                f"{rendered_name}": db_field_and_render_fn[1](
                    dict_record.get(db_field_and_render_fn[0], "")
                ),
            },
            **{"id": record.id},
        )
    return out


def _view_all_records(
    render_mapper: Optional[Dict[str, Tuple[str, Callable]]] = None,
    collection_name: str = "articles",
) -> List[Dict[str, str]]:
    output_list = list()
    _, _, _, list_in_first_tab = _make_db_connection(collection_name)
    for record in list_in_first_tab:
        output_list.append(_view_record(record, render_mapper=render_mapper))
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


@articles_blue.route("/getallsyntheses", endpoint="getallsyntheses", methods=["GET"])
def get_all_syntheses():
    return _view_all_records(
        collection_name="syntheses", render_mapper=SYNTHESIS_RENDER_MAPPER
    )


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
        db, ARTICLES_COLLECTION, doc_id=doc_id, db_insert_dict=db_insert_dict
    )
    return request_dict


@articles_blue.route("/getreadstatus", endpoint="/getreadstatus", methods=["POST"])
def get_read_status():
    request_dict: Dict[str, str] = json.loads(request.data.decode("utf-8"))
    db, doc_ref, _, _ = _make_db_connection()
    doc: DocumentReference = doc_ref.document(request_dict.get("id"))
    return {"read_status": doc.get().to_dict().get("ReadStatus")}


@articles_blue.route(
    "/explainercontent", endpoint="/explainercontent", methods=["POST"]
)
def explainer_content():
    request_dict: Dict[str, str] = json.loads(request.data.decode("utf-8"))
    doc_id: str = request_dict.get("id")
    db, doc_ref, _, _ = _make_db_connection()
    logger.warn(f"Request dict: {request_dict}")
    prompt = f"""{request_dict.get(EXPLAINED_CONTENT_KEY)}"""
    article_doc: Dict[str, str] = (
        db.collection(ARTICLES_COLLECTION).document(doc_id).get().to_dict()
    )
    current_explained_content: str = article_doc.get(EXPLAINED_CONTENT_KEY_DB)
    if current_explained_content:
        prompt = prompt.split(current_explained_content)[1]
    else:
        current_explained_content = ""
    prompt_to_model = prompt.replace("${article}", article_doc.get(CLEANED_TEXT_KEY_DB))
    logger.warn(f"Prompt to model: {prompt_to_model}")
    explained_content = call_model_endpoint(prompt_to_model, model=MODEL_ENGINE_LARGE)
    request_dict.pop("id")
    request_dict.update(
        {
            EXPLAINED_CONTENT_KEY: current_explained_content
            + "\n"
            + prompt
            + "\n"
            + explained_content
        }
    )
    logger.warn(f"Request dict: {request_dict}")
    db_insert_dict = {
        RENDER_MAPPER.get(key)[0]: value for key, value in request_dict.items()
    }
    add_synchronous_components_to_db(
        db, ARTICLES_COLLECTION, doc_id=doc_id, db_insert_dict=db_insert_dict
    )
    return json.dumps({"success": True}), 200, {"ContentType": "application/json"}


@articles_blue.route("/createsynthesis", endpoint="/createsynthesis", methods=["POST"])
def create_synthesis():
    request_dict: Dict[str, str] = json.loads(request.data.decode("utf-8"))
    ids: Optional[List[str], None] = request_dict.get("ids")
    db, doc_ref, _, _ = _make_db_connection()
    out_content: Dict[str, List[str, str, str]] = dict()
    for id in ids:
        out_content.update(
            {
                id: [
                    doc_ref.document(id).get().to_dict().get(AUTOSUMMARY_KEY_DB),
                    doc_ref.document(id).get().to_dict().get(URL_INPUT_KEY_DB),
                    doc_ref.document(id).get().to_dict().get(NAME_INPUT_KEY_DB),
                ]
            }
        )

    synthesis_prompt = f"""Provide a synthesis of the following {len(ids)} texts.
    Focus on where they agree and differ, providing an overview of where
    their authors stand on the topic. Please provide your answers in markdown bullet points. \n"""
    i = 1
    for id, text in out_content.items():
        synthesis_prompt += f" \n {text[2]}: {text[0]}"
        i += 1

    model_synthesis = call_model_endpoint(synthesis_prompt)
    title = call_model_endpoint(
        f"Give a title to the following text: {model_synthesis}"
    )
    doc_id = create_doc_id()
    doc_ref = db.collection(SYNTHESIS_COLLECTION).document(doc_id)
    doc_ref.set(
        {
            ID_LIST_KEY_DB: ids,
            SYNTHESIS_KEY_DB: model_synthesis,
            SYNTHESIS_TITLE_KEY_DB: title,
            URL_LIST_KEY_DB: [value[1] for keys, value in out_content.items()],
            NAME_LIST_KEY_DB: [value[2] for keys, value in out_content.items()],
        }
    )
    return json.dumps({"success": True}), 200, {"ContentType": "application/json"}


@articles_blue.route("/getalldailynotes", endpoint="/getalldailynotes", methods=["GET"])
def create_synthesis():
    return _view_all_records(
        collection_name=DAILY_NOTES_COLLECTION, render_mapper=DAILY_NOTE_RENDER_MAPPER
    )


@articles_blue.route("/updatedailynote", endpoint="/updatedailynote", methods=["POST"])
def update_daily_note():
    request_dict: Dict[str, str] = json.loads(request.data.decode("utf-8"))
    doc_id: str = request_dict.get("id")
    db, doc_ref, _, _ = _make_db_connection()
    logger.warn(f"Request dict: {request_dict}")
    daily_note_addition = f"""{request_dict.get(DAILY_NOTE_TEXT_KEY)}"""
    article_doc: Dict[str, str] = (
        db.collection(DAILY_NOTES_COLLECTION).document(doc_id).get().to_dict()
    )
    current_daily_note_text: str = article_doc.get(DAILY_NOTE_TEXT_KEY_DB)
    logger.warn(f"Current daily note: {current_daily_note_text}")
    logger.warn(f"Daily note addition: {daily_note_addition}")
    if current_daily_note_text:
        daily_note_addition = daily_note_addition.split(current_daily_note_text)
        logger.warn(f"Split: {daily_note_addition}")
        daily_note_addition = daily_note_addition[1]
    else:
        current_daily_note_text = ""
    model_prompts = re.findall(r"{QUESTION:(.*?)}", daily_note_addition)
    if model_prompts:
        model_output = ""
        daily_note_addition = re.sub(r"{QUESTION:(.*?)}", "", daily_note_addition)
        for prompt in model_prompts:
            new_model_output = call_model_endpoint(prompt, model=MODEL_ENGINE_LARGE)
            model_output += f"{prompt}: {new_model_output}"
        daily_note_addition += model_output
    request_dict.pop("id")
    request_dict.update(
        {DAILY_NOTE_TEXT_KEY: current_daily_note_text + "\n" + daily_note_addition}
    )
    logger.warn(f"Request dict: {request_dict}")
    db_insert_dict = {
        DAILY_NOTE_RENDER_MAPPER.get(key)[0]: value
        for key, value in request_dict.items()
    }
    add_synchronous_components_to_db(
        db, DAILY_NOTES_COLLECTION, doc_id=doc_id, db_insert_dict=db_insert_dict
    )
    return json.dumps({"success": True}), 200, {"ContentType": "application/json"}


@articles_blue.route(
    "/createnewdailynote", endpoint="/createnewdailynote", methods=["GET"]
)
def create_new_daily_note():
    db, doc_ref, _, list_refs = _make_db_connection(
        collection_name=DAILY_NOTES_COLLECTION
    )
    logger.warn(list_refs)
    today_date = datetime.datetime.today().date().strftime("%Y/%m/%d")
    last_date_db = list_refs[0].to_dict().get(DATE_INPUT_KEY_DB)
    logger.warn(last_date_db)
    logger.warn(today_date)
    if today_date != last_date_db:
        add_synchronous_components_to_db(
            db, DAILY_NOTES_COLLECTION, db_insert_dict={DATE_INPUT_KEY_DB: today_date}
        )
    return json.dumps({"success": True}), 200, {"ContentType": "application/json"}
