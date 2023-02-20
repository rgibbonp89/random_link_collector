import streamlit as st
from google.cloud import firestore
import os
from pages.pages_utils.search_bar import local_css, remote_css

st.set_page_config(page_title="Articles")

db = firestore.Client.from_service_account_json("./.keys/firebase.json")
doc_ref = db.collection("articles")

docs = doc_ref.stream()

recent_tab, search_tab = st.tabs(["Recent", "Search", "All"])

list_in_first_tab = [doc for doc in docs]

## make functions out of the below
## create text entry
## how will it update the firestore DB? post request?
## in the initial chatgpt entry, async/await entry into the firestore DB?
## what tech is needed for this?


with recent_tab:
    for l in list_in_first_tab:
        with st.expander(l.to_dict()["Name"]):
            with st.container():
                edit = st.radio(
                    f"""Edit: "{l.to_dict()["Name"]}"?""", [True, False], index=1
                )
                if edit:
                    with st.form(f"""Edit {l.to_dict()["Name"]}"""):
                        st.text_input("Article name: ", value=l.to_dict()["Name"])
                        st.text_input("Article url: ", value=l.to_dict()["URL"])
                        st.text_area("Auto-summary: ", l.to_dict()["AutoSummary"])
                        submit_changes = st.form_submit_button("OK")

                else:
                    st.write("Article name: ", l.to_dict()["Name"])
                    st.write("Article url: ", l.to_dict()["URL"])
                    st.write("Auto-summary: ", l.to_dict()["AutoSummary"])

with search_tab:
    local_css("./app/pages/style.css")
    remote_css("https://fonts.googleapis.com/icon?family=Material+Icons")
    selected = st.text_input("", "")
    button_clicked = st.button("OK")
