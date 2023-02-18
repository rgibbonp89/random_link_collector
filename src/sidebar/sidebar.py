import time
import streamlit as st


def create_sidebar() -> None:
    """Add sidebar component"""
    with st.sidebar:
        with st.echo():
            st.write("This code will be printed to the sidebar.")

        with st.spinner("Loading..."):
            time.sleep(5)
        st.success("Done!")
