import streamlit as st
from google.cloud import firestore
from google.cloud.firestore_v1 import Client, CollectionReference
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

with recent_tab:
    for l in list_in_first_tab:
        with st.expander(l.to_dict()["Name"]):
            with st.container():
                edit = st.radio(
                    f"""Edit: "{l.to_dict()["Name"]}"?""",
                    options=[True, False],
                    index=1,
                )
                if edit:
                    with st.form(f"""Edit {l.to_dict()["Name"]}"""):
                        name = st.text_input(
                            "Article name: ", value=l.to_dict()["Name"]
                        )
                        article_url = st.text_input(
                            "Article url: ", value=l.to_dict()["URL"]
                        )
                        autosummary = st.text_area(
                            "Auto-summary: ", l.to_dict().get("AutoSummary")
                        )
                        mysummary = st.text_area(
                            "My summary: ", l.to_dict().get("MySummary")
                        )
                        submit_changes = st.form_submit_button("OK")
                        if submit_changes:
                            doc_ref.document(l.id).set(
                                {
                                    "Name": name,
                                    "URL": article_url,
                                    "AutoSummary": autosummary,
                                    "MySummary": mysummary,
                                }
                            )
                else:
                    st.write("Article name: ", l.to_dict()["Name"])
                    st.write("Article url: ", l.to_dict()["URL"])
                    st.write("Auto-summary: ", l.to_dict().get("AutoSummary"))
                    st.write("My summary: ", l.to_dict().get("MySummary"))


mapper = {
    "My summary": "MySummary",
    "Auto-summary": "AutoSummary",
    "Name": "Name",
    "URL": "URL",
}

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
            if fuzz.token_sort_ratio(r_doc.to_dict().get(mapper.get(option)), selection)
            > search_strictness
        ]
        for r in result_docs_pruned:
            with st.expander(r.to_dict().get("Name")):
                st.write("Article name: ", r.to_dict()["Name"])
                st.write("Article url: ", r.to_dict()["URL"])
                st.write("Auto-summary: ", r.to_dict().get("AutoSummary"))
                st.write("My summary: ", r.to_dict().get("MySummary"))
