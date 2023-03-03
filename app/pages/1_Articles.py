from typing import List, Dict, Tuple, Callable, Optional

import streamlit as st
from google.cloud import firestore
from google.cloud.firestore_v1 import Client, CollectionReference, DocumentSnapshot
from pathlib import Path
from pages.pages_utils.search_bar import local_css, remote_css
from fuzzywuzzy import fuzz


SEARCH_STRICTNESS_CONSTANT = 30

st.set_page_config(page_title="Articles")

db: Client = firestore.Client.from_service_account_json(
    f"{Path(__file__).parent.parent.parent}/.keys/firebase.json"
)
doc_ref: CollectionReference = db.collection("articles")

docs = doc_ref.stream()

recent_tab, search_tab = st.tabs(["Recent", "Search"])

list_in_first_tab = sorted(
    [doc for doc in docs], key=lambda x: x.create_time, reverse=True
)

TextArea: str = "text_area"
TextInput: str = "text_input"


RENDER_MAPPER: Dict[str, Tuple[str, str, Callable]] = {
    "My summary": ("MySummary", TextArea, lambda x: x),
    "Auto-summary": (
        "AutoSummary",
        TextArea,
        lambda x: x.replace("• ", "* ").replace("- ", "* "),
    ),
    "Name": ("Name", TextInput, lambda x: x),
    "URL": ("URL", TextInput, lambda x: x),
}


def _view_and_edit_record(
    record: DocumentSnapshot,
    radio_button_edit_contents: str = """Edit: "{contents}"?""",
    radio_button_render_name: str = """Edit {contents}""",
):
    with st.container():
        edit = st.radio(
            radio_button_edit_contents.format(contents=record.to_dict()["Name"]),
            options=[True, False],
            index=1,
        )
        if edit:
            with st.form(
                radio_button_render_name.format(contents=record.to_dict()["Name"])
            ):
                render_components: Dict[str, str] = {}
                for rendered_name, db_field_and_render_fn in RENDER_MAPPER.items():
                    render_components.update(
                        {
                            db_field_and_render_fn[0]: st.text_area(
                                f"{rendered_name}: ",
                                value=record.to_dict()[db_field_and_render_fn[0]],
                            )
                            if db_field_and_render_fn[1] == TextArea
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
                        {
                            **{
                                db_field: input
                                for db_field, input in render_components.items()
                            }
                        }
                    )
                if delete_records:
                    doc_ref.document(record.id).delete()
        else:
            for rendered_name, db_field_and_render_fn in RENDER_MAPPER.items():
                st.write(
                    f"{rendered_name}: ",
                    db_field_and_render_fn[2](
                        record.to_dict()[db_field_and_render_fn[0]]
                    ),
                )


with recent_tab:
    for l in list_in_first_tab:
        with st.expander(l.to_dict()["Name"]):
            _view_and_edit_record(l)


with search_tab:
    local_css(f"{Path(__file__).parent}/style.css")
    remote_css("https://fonts.googleapis.com/icon?family=Material+Icons")
    selection = st.text_input("Search term", "")
    search_strictness = st.text_input(
        "Strictness",
    )
    option = st.selectbox("Search field", ("Name", "URL", "Auto-summary", "My summary"))
    button_clicked = st.button("OK")
    if button_clicked:
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
            with st.expander(r.to_dict().get("Name")):
                _view_and_edit_record(
                    r,
                    radio_button_edit_contents="""Edit retrieved {contents}?""",
                    radio_button_render_name="""Edit retrieved {contents}""",
                )
