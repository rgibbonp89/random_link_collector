import json
from typing import Dict, Tuple, Callable, List
from flask import Blueprint, request
import streamlit as st
from google.cloud import firestore
from google.cloud.firestore_v1 import (
    Client,
    CollectionReference,
    DocumentReference,
    DocumentSnapshot,
)
from pathlib import Path
from fuzzywuzzy import fuzz


articles_blue = Blueprint("articlesblue", __name__)


SEARCH_STRICTNESS_CONSTANT = 95
SEARCH_STRICTNESS_KEY = "search_strictness"

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


def edit_record(record):
    # this will be the edit record flow
    render_components: Dict[str, str] = {}
    for rendered_name, db_field_and_render_fn in RENDER_MAPPER.items():
        render_components.update(
            {
                db_field_and_render_fn[0]: st.text_area(
                    f"{rendered_name}: ",
                    value=record.to_dict()[db_field_and_render_fn[0]],
                )
                if db_field_and_render_fn[1]
                else st.text_input(
                    f"{rendered_name}: ",
                    value=record.to_dict()[db_field_and_render_fn[0]],
                )
            }
        )
        submit_changes = st.form_submit_button("OK")
        delete_records = st.form_submit_button("X")
        if submit_changes:
            doc_ref.document(record.id).set(
                {**{db_field: input for db_field, input in render_components.items()}}
            )
        if delete_records:
            doc_ref.document(record.id).delete()


def search_records(search_strictness, option, selection):
    for l in list_in_first_tab:
        _view_record(l)
        search_strictness = (
            int(search_strictness)
            if search_strictness is not None
            else SEARCH_STRICTNESS_CONSTANT
        )
        result_docs = doc_ref.stream()
        result_docs_pruned = [
            r_doc
            for r_doc in result_docs
            if fuzz.token_sort_ratio(
                r_doc.to_dict().get(RENDER_MAPPER.get(option)[0]), selection
            )
            > search_strictness
        ]
        for r in result_docs_pruned:
            _view_record(r)


@articles_blue.route("/getarticles", endpoint="getarticles", methods=["GET"])
def get_articles():
    return _view_all_records()


@articles_blue.route("/updaterecord", endpoint="updaterecord", methods=["POST"])
def update_article():
    request_dict: Dict[str, str] = json.loads(request.data.decode("utf-8"))
    search_strictness = int(
        request_dict.get(SEARCH_STRICTNESS_KEY, SEARCH_STRICTNESS_CONSTANT)
    )
    result_docs = doc_ref.stream()
    result_docs_pruned: List[DocumentSnapshot] = [
        r_doc
        for r_doc in result_docs
        if fuzz.token_sort_ratio(r_doc.to_dict().get("Name"), request_dict.get("Name"))
        > search_strictness
    ]
    number_results_found = len(result_docs_pruned)
    assert number_results_found <= 1
    request_dict.pop(SEARCH_STRICTNESS_KEY, None)
    doc_ref.document(result_docs_pruned[0].id).update(
        request_dict
    ) if number_results_found != 0 else print("No matches found")
    return json.dumps({"success": True}), 200, {"ContentType": "application/json"}
