import streamlit as st
from pathlib import Path
import logging

from utils.config import DMCConfig


# @st.cache_data
def get_config() -> DMCConfig:
    # initialize / default path
    path_to_config = None
    # file name and potential paths
    file_name = "config.toml"
    potential_paths = ["", ".streamlit"]
    # check potential paths
    for p in potential_paths:
        path_to_config_ = Path(p) / file_name
        logging.debug(f"path_to_config={path_to_config_.as_posix()}.exists(): {path_to_config_.exists()}")
        if path_to_config_.exists():
            path_to_config = path_to_config_
            break

    # read config file
    return DMCConfig(path_to_config, "default_config.toml")


def config_page_head(
        page_title: str,
        page_icon: str = "💡",
):
    # configure page => set favicon and page title
    st.set_page_config(page_title=page_title, page_icon=page_icon)  #  chr(int(" U+1F4A1"[2:], 16)) # https://emojipedia.org/  chr(int("U+1F6A8"[2:], 16))

    # hide "made with Streamlit" text in footer
    hide_streamlit_style = """
                <style>
                #MainMenu {visibility: hidden;}
                footer {visibility: hidden;}
                </style>
                """
    st.markdown(hide_streamlit_style, unsafe_allow_html=True)

    # Text
    config = get_config()

    st.title(config["APP_TITLE"])

    if config["APP_HEADER"]:
        st.header(config["APP_HEADER"])
    if config["APP_SUBHEADER"]:
        st.subheader(config["APP_SUBHEADER"])
    if config["APP_TEXT"]:
        st.write(config["APP_TEXT"])
    return config
