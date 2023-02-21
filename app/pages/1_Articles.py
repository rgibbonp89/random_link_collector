import streamlit as st
from google.cloud import firestore
from google.cloud.firestore_v1 import Client
from pathlib import Path
from pages.pages_utils.search_bar import local_css, remote_css

st.set_page_config(page_title="Articles")

db: Client = firestore.Client.from_service_account_json(
    f"{Path(__file__).parent.parent.parent}/.keys/firebase.json"
)
doc_ref = db.collection("articles")

docs = doc_ref.stream()

recent_tab, search_tab = st.tabs(["Recent", "Search"])

list_in_first_tab = [doc for doc in docs]


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
                            "Auto-summary: ", l.to_dict()["AutoSummary"]
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
                    st.write("Auto-summary: ", l.to_dict()["AutoSummary"])
                    st.write("My summary: ", l.to_dict().get("MySummary"))

with search_tab:
    local_css(f"{Path(__file__).parent}/style.css")
    remote_css("https://fonts.googleapis.com/icon?family=Material+Icons")
    selected = st.text_input("", "")
    button_clicked = st.button("OK")
