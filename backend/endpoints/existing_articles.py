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
from backend.integrations.model_endpoint import call_model_endpoint, Models
from backend.integrations.utils.utils import (
    add_synchronous_components_to_db,
    _make_db_connection,
    create_doc_id,
    SYNTHESIS_RENDER_MAPPER,
    RENDER_MAPPER,
    FrontendReferences,
    DB,
    DAILY_NOTE_RENDER_MAPPER,
    DBReferences,
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
    (
        db,
        doc_ref,
        docs,
        list_in_first_tab,
        doc_id,
        request_dict,
    ) = preprocess_request_and_make_db_connection(request)
    doc_ref.document(doc_id).delete()
    return json.dumps({"success": True}), 200, {"ContentType": "application/json"}


def preprocess_request_and_make_db_connection(api_request):
    request_dict: Dict[str, str] = json.loads(api_request.data.decode("utf-8"))
    db, doc_ref, docs, list_in_first_tab = _make_db_connection()
    doc_id = request_dict.get("id")
    return db, doc_ref, docs, list_in_first_tab, doc_id, request_dict


@articles_blue.route("/updatearticle", endpoint="/updatearticle", methods=["POST"])
def update_article_flow():
    (
        db,
        doc_ref,
        docs,
        list_in_first_tab,
        doc_id,
        request_dict,
    ) = preprocess_request_and_make_db_connection(request)
    request_dict.pop("id")
    db_insert_dict = {
        RENDER_MAPPER.get(key)[0]: value for key, value in request_dict.items()
    }
    add_synchronous_components_to_db(
        db, DB.ARTICLES_COLLECTION, doc_id=doc_id, db_insert_dict=db_insert_dict
    )
    return request_dict


@articles_blue.route("/getreadstatus", endpoint="/getreadstatus", methods=["POST"])
def get_read_status():
    (
        db,
        doc_ref,
        docs,
        list_in_first_tab,
        doc_id,
        request_dict,
    ) = preprocess_request_and_make_db_connection(request)
    doc: DocumentReference = doc_ref.document(doc_id)
    return {"read_status": doc.get().to_dict().get("ReadStatus")}


@articles_blue.route(
    "/explainercontent", endpoint="/explainercontent", methods=["POST"]
)
def explainer_content():
    (
        db,
        doc_ref,
        docs,
        list_in_first_tab,
        doc_id,
        request_dict,
    ) = preprocess_request_and_make_db_connection(request)
    logger.warn(f"Request dict: {request_dict}")
    prompt = f"""{request_dict.get(FrontendReferences.EXPLAINED_CONTENT_KEY)}"""
    article_doc: Dict[str, str] = (
        db.collection(DB.ARTICLES_COLLECTION).document(doc_id).get().to_dict()
    )
    current_explained_content: str = article_doc.get(
        DBReferences.EXPLAINED_CONTENT_KEY_DB
    )
    if current_explained_content:
        prompt = prompt.split(current_explained_content)[1]
    else:
        current_explained_content = ""
    if "${article}" in prompt:
        prompt_to_model = prompt.replace(
            "${article}", article_doc.get(DBReferences.CLEANED_TEXT_KEY_DB)
        )
    else:
        prompt_to_model = prompt
    logger.warn(f"Prompt to model: {prompt_to_model}")
    explained_content = call_model_endpoint(
        prompt_to_model, model=Models.MODEL_ENGINE_LARGE
    )
    request_dict.pop("id")
    request_dict.update(
        {
            FrontendReferences.EXPLAINED_CONTENT_KEY: current_explained_content
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
        db, DB.ARTICLES_COLLECTION, doc_id=doc_id, db_insert_dict=db_insert_dict
    )
    return json.dumps({"success": True}), 200, {"ContentType": "application/json"}


@articles_blue.route("/createsynthesis", endpoint="/createsynthesis", methods=["POST"])
def create_synthesis():
    (
        db,
        doc_ref,
        docs,
        list_in_first_tab,
        doc_id,
        request_dict,
    ) = preprocess_request_and_make_db_connection(request)
    ids: Optional[List[str], None] = request_dict.get("ids")
    out_content: Dict[str, List[str, str, str]] = dict()
    for id in ids:
        out_content.update(
            {
                id: [
                    doc_ref.document(id)
                    .get()
                    .to_dict()
                    .get(DBReferences.AUTOSUMMARY_KEY_DB),
                    doc_ref.document(id)
                    .get()
                    .to_dict()
                    .get(DBReferences.URL_INPUT_KEY_DB),
                    doc_ref.document(id)
                    .get()
                    .to_dict()
                    .get(DBReferences.NAME_INPUT_KEY_DB),
                ]
            }
        )

    synthesis_prompt = f"""Provide a synthesis of the following {len(ids)} texts.
    Focus on where they agree and differ, providing an overview of where
    the articles stand on the topic. Please provide your answers in markdown bullet points. \n"""
    i = 1
    for id, text in out_content.items():
        synthesis_prompt += f" \n {text[2]}: {text[0]}"
        i += 1

    model_synthesis = call_model_endpoint(
        synthesis_prompt, model=Models.MODEL_ENGINE_LARGE
    )
    title = call_model_endpoint(
        f"Give a title to the following text: {model_synthesis}"
    )
    doc_id = create_doc_id()
    doc_ref = db.collection(DB.SYNTHESIS_COLLECTION).document(doc_id)
    doc_ref.set(
        {
            DBReferences.ID_LIST_KEY_DB: ids,
            DBReferences.SYNTHESIS_KEY_DB: model_synthesis,
            DBReferences.SYNTHESIS_TITLE_KEY_DB: title,
            DBReferences.URL_LIST_KEY_DB: [
                value[1] for keys, value in out_content.items()
            ],
            DBReferences.NAME_LIST_KEY_DB: [
                value[2] for keys, value in out_content.items()
            ],
        }
    )
    return json.dumps({"success": True}), 200, {"ContentType": "application/json"}


@articles_blue.route("/getalldailynotes", endpoint="/getalldailynotes", methods=["GET"])
def create_synthesis():
    return _view_all_records(
        collection_name=DB.DAILY_NOTES_COLLECTION,
        render_mapper=DAILY_NOTE_RENDER_MAPPER,
    )


@articles_blue.route("/updatedailynote", endpoint="/updatedailynote", methods=["POST"])
def update_daily_note():
    (
        db,
        doc_ref,
        docs,
        list_in_first_tab,
        doc_id,
        request_dict,
    ) = preprocess_request_and_make_db_connection(request)
    logger.warn(f"Request dict: {request_dict}")
    daily_note_addition = (
        f"""{request_dict.get(FrontendReferences.DAILY_NOTE_TEXT_KEY)}"""
    )
    article_doc: Dict[str, str] = (
        db.collection(DB.DAILY_NOTES_COLLECTION).document(doc_id).get().to_dict()
    )
    current_daily_note_text: str = article_doc.get(DBReferences.DAILY_NOTE_TEXT_KEY_DB)
    logger.warn(f"Current daily note: {current_daily_note_text}")
    logger.warn(f"Daily note addition: {daily_note_addition}")
    if current_daily_note_text:
        daily_note_addition = daily_note_addition.split(current_daily_note_text)
        daily_note_addition = daily_note_addition[1]
    else:
        current_daily_note_text = ""
    model_prompts = re.findall(r"{QUESTION:(.*?)}", daily_note_addition)
    if model_prompts:
        model_output = ""
        daily_note_addition = re.sub(r"{QUESTION:(.*?)}", "", daily_note_addition)
        for prompt in model_prompts:
            new_model_output = call_model_endpoint(
                prompt, model=Models.MODEL_ENGINE_LARGE
            )
            model_output += f"{prompt}: {new_model_output}"
        daily_note_addition += model_output
    request_dict.pop("id")
    request_dict.update(
        {
            FrontendReferences.DAILY_NOTE_TEXT_KEY: current_daily_note_text
            + "\n"
            + daily_note_addition
        }
    )
    logger.warn(f"Request dict: {request_dict}")
    db_insert_dict = {
        DAILY_NOTE_RENDER_MAPPER.get(key)[0]: value
        for key, value in request_dict.items()
    }
    add_synchronous_components_to_db(
        db, DB.DAILY_NOTES_COLLECTION, doc_id=doc_id, db_insert_dict=db_insert_dict
    )
    return json.dumps({"success": True}), 200, {"ContentType": "application/json"}


@articles_blue.route(
    "/createnewdailynote", endpoint="/createnewdailynote", methods=["GET"]
)
def create_new_daily_note():
    db, doc_ref, _, list_refs = _make_db_connection(
        collection_name=DB.DAILY_NOTES_COLLECTION
    )
    logger.warn(list_refs)
    today_date = datetime.datetime.today().date().strftime("%Y/%m/%d")
    last_date_db = list_refs[0].to_dict().get(DBReferences.DATE_INPUT_KEY_DB)
    logger.warn(last_date_db)
    logger.warn(today_date)
    if today_date != last_date_db:
        add_synchronous_components_to_db(
            db,
            DB.DAILY_NOTES_COLLECTION,
            db_insert_dict={DBReferences.DATE_INPUT_KEY_DB: today_date},
        )
    return json.dumps({"success": True}), 200, {"ContentType": "application/json"}
