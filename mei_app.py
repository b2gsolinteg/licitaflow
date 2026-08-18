import streamlit as st

st.set_page_config(
    page_title="LicitaNexo MEI",
    page_icon="🔎",
    layout="wide",
    initial_sidebar_state="expanded",
)

from src.mei_preview6_app import main


if __name__ == "__main__":
    main()
