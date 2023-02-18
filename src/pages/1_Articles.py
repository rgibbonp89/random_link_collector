import streamlit as st

from pages.pages_utils.search_bar import local_css, remote_css

st.set_page_config(page_title="Articles")

recent_tab, search_tab, all_tab = st.tabs(["Recent", "Search", "All"])

list_in_first_tab = [
    "Do riots affect voting habits?",
    "Does GDP correlate with civil war?",
    "FT editorial article",
]


with recent_tab:
    for l in list_in_first_tab:
        with st.expander(l):
            with st.container():
                edit = st.radio(f"""Edit: "{l}"?""", [True, False], index=1)
                if edit:
                    with st.form("Edit article contents"):
                        st.text_input("Article name: ", "Bla")
                        st.text_input("Article url: ", "www.google.com")
                        st.text_input("Auto-summary: ", "Text")
                        st.text_input("My summary: ", "Text")
                        submit_changes = st.form_submit_button("OK")
                else:
                    st.write("Article name: ", "Bla")
                    st.write("Article url: ", "www.google.com")
                    st.write("Auto-summary: ", "Text")
                    st.write("My summary: ", "Text")


with search_tab:
    local_css("./src/pages/style.css")
    remote_css("https://fonts.googleapis.com/icon?family=Material+Icons")
    selected = st.text_input("", "")
    button_clicked = st.button("OK")

with all_tab:
    with st.expander("See explanation"):
        st.markdown("## Some header text")
