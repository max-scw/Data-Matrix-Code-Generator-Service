import streamlit as st
import uuid
import logging
import sys

from DataMatrixCode import (
    FORMAT_ANSI_MH_10,
    message_formats,
    DataMatrixCode,
    validate_envelope_format
)
from utils.utils import rstrip_non_ascii_characters
from utils.config import DMCConfig
from utils.utils_streamlit import config_page_head
from utils.env_vars import get_env_variable, cast_logging_level


from typing import Dict

# global constants
DI_FORMAT = FORMAT_ANSI_MH_10
FORMAT_MAPPING = message_formats(DI_FORMAT).get_di_mapping()
# print(f"global: FORMAT_MAPPING={FORMAT_MAPPING.keys()}")


def create_unique_key():
    return int(uuid.uuid4())


def clear_rows():
    st.session_state.rows = [Row()]


class Row:
    def __init__(self) -> None:
        self.key_select_box = create_unique_key()
        self.key_text_box = create_unique_key()
        self.text_input = None
        self.selected_option = None
        # self.description = None

    def __repr__(self) -> str:
        return f"Row({self.key_select_box}, {self.selected_option}, {self.key_text_box}, {self.text_input}, {self.description})"

    @property
    def description(self) -> str:
        return FORMAT_MAPPING[self.selected_option]["Explanation"]


def create_row(options, row: Row):
    columns = st.columns([1, 3])
    with columns[0]:
        row.selected_option = st.selectbox(
            "Select Option:",
            options,
            key=row.key_select_box
        )
    with columns[1]:
        row.text_input = rstrip_non_ascii_characters(st.text_input(
            "Content:",
            value=row.text_input if row.text_input else "",
            key=row.key_text_box,
            help=row.description
        ))


def draw_rows(options, container, add_row: bool = False):

    if add_row:
        add_row_ = True
        # check if any row has no content
        for row in st.session_state.rows:
            if (row.text_input is None) or (row.text_input == ""):
                add_row_ = False
                break

        if add_row_:
            st.session_state.rows.append(Row())

    with container:
        for row in st.session_state.rows:
            create_row(options, row)


def clear_empty_rows():
    rows_ = []
    for row in st.session_state.rows:
        if (row.text_input is not None) and (row.text_input != ""):
            rows_.append(row)
    st.session_state.rows = rows_


def check_for_duplicate_rows():
    ids = [row.selected_option for row in st.session_state.rows if (row.text_input is not None) and (row.text_input != "")]
    if len(ids) != len(set(ids)):
        st.warning(f"Rows should have unique values. Duplicated entries are ignored.")


def check_format(strict: bool = True) -> (Dict[str, str], bool):

    message_fields = dict()
    invalid = False
    for row in st.session_state.rows:
        if (row.text_input is not None) and (not row.text_input == ""):
            data_identifier = row.selected_option
            content = row.text_input

            _, flag_valid = validate_envelope_format({DI_FORMAT: [data_identifier + content]})
            logging.debug(f"{row}: {flag_valid}")

            if not flag_valid:
                msg = f"The value '{content}' for data identifier '{data_identifier}' does not comply with the format " \
                      f"specifications: {FORMAT_MAPPING[data_identifier]['Meta Data']}.",
                logging.warning(msg)
                if strict:
                    st.error(msg, icon="🚨")
                else:
                    st.warning(msg, icon="⚠️")
            else:
                message_fields[data_identifier] = content

            invalid |= not flag_valid

    return message_fields, invalid


# ---- Config
def initialize_options(config: DMCConfig):
    # default values
    if "DMC_USE_MESSAGE_ENVELOPE" not in st.session_state:
        st.session_state.use_message_envelope = config["DMC_USE_MESSAGE_ENVELOPE"]

    if "DMC_USE_FORMAT_ENVELOPE" not in st.session_state:
        st.session_state.use_format_envelope = config["DMC_USE_FORMAT_ENVELOPE"]

    if "DMC_RECTANGULAR_CODE" not in st.session_state:
        st.session_state.use_rectangular = config["DMC_RECTANGULAR_CODE"]

    if "DMC_NUMBER_QUIET_ZONE_MODULES" not in st.session_state:
        st.session_state.n_quiet_zone_modules = config["DMC_NUMBER_QUIET_ZONE_MODULES"]

    if "APP_OPTIONS_EXPANDED" not in st.session_state:
        st.session_state.options_expanded = False


def draw_options():
    # options container
    with st.expander("Options", expanded=st.session_state.options_expanded):
        columns = st.columns([1, 1], gap="large")
        with columns[0]:
            st.markdown("*Message string options*")
            st.session_state.use_message_envelope = st.checkbox(
                "message envelope",
                value=st.session_state.use_message_envelope,
                key=None,
                help=None
            )
            st.session_state.use_format_envelope = st.checkbox(
                "format envelope",
                value=st.session_state.use_format_envelope,
                key=None,
                help=None
            )
            # st.markdown("*App options*")
            # st.session_state.explain_data_identifiers = st.checkbox(
            #     "explain Data Identifiers",
            #     value=st.session_state.explain_data_identifiers,
            #     key=None,
            #     help="Shows info message when drop-down menu for *Data Identifier* changes."
            # )
        with columns[1]:
            st.markdown("*Data-Matrix-Code generator options*")
            st.session_state.use_rectangular = st.checkbox(
                "rectangular DMC",
                value=st.session_state.use_rectangular,
                help="Should a rectangular DMC be generated?"
            )
            st.session_state.n_quiet_zone_modules = st.number_input(
                r"\# moduls for quiet zone",
                label_visibility="visible",
                min_value=0,
                max_value=10,
                value=st.session_state.n_quiet_zone_modules,
                help="Number of empty (white) moduls that frame the DMC",
            )


# ---- DMC related functions
def draw_results(img, message_string: str, n_ascii_characters: int):
    columns = st.columns([5, 1], gap="small")

    with columns[0]:
        tabs = st.tabs(["Image", "Message String"])
        with tabs[0]:
            st.image(img, caption=message_string)
        # with tabs[1]:
        #     # st.table({enc: str(message_string.encode(encoding=enc)) for enc in ["UTF-8", "unicode-escape"]})
        #     encodings = {"backslash-replace": message_string.encode("utf-8", "backslashreplace").decode("utf-8",
        #                                                                                                 "backslashreplace"),
        #                  "XML char reference replace": message_string.encode("utf-8", "xmlcharrefreplace").decode(
        #                      "utf-8",
        #                      "xmlcharrefreplace"),
        #                  "named replace": message_string.encode("utf-8", "namereplace").decode("utf-8", "namereplace"),
        #                  "hex": binascii.hexlify(message_string.encode("utf-8")),
        #                  "base64": binascii.b2a_base64(message_string.encode("utf-8")),
        #                  "ord": [ord(el) for el in message_string]
        #                  }
        #     for enc, string in encodings.items():
        #         st.write(f"encoding: {enc}")
        #         st.write(string)

    with columns[1]:
        st.metric("#ASCII characters", n_ascii_characters)


# ----- App
def main():
    config = config_page_head("DMC Generator", page_icon="💡")

    initialize_options(config)

    # Initialize a list to store the dropdown options
    options = list(FORMAT_MAPPING.keys())

    if "rows" not in st.session_state:
        st.session_state.rows = [Row()]

    placeholder = st.container()

    # add buttons
    with st.container():
        columns = st.columns([1, 1, 1, 3, 1], gap="small")
        with columns[0]:
            add = st.button(
                label="add",
                type="secondary",
                use_container_width=True,
                help="Add new row",
            )
        with columns[1]:
            st.button(
                label="clear",
                type="secondary",
                on_click=clear_empty_rows,
                use_container_width=True,
                help="Clear empty rows.",
            )
        with columns[2]:
            st.button(
                label="reset",
                type="secondary",
                on_click=clear_rows,
                use_container_width=True,
                help="Clear all rows.",
            )
        with columns[4]:
            generate_dmc = st.button(
                label="generate",
                type="primary",
                use_container_width=True,
                help="Generate a Data-Matrix code",
                # on_click=print("click generate"),
            )

    draw_rows(options, placeholder, add)

    draw_options()

    # for row in st.session_state.rows:  # FIXME: for debugging only
    #     logging.debug(row)
    # logging.debug("___")

    if generate_dmc:
        check_for_duplicate_rows()
        message_fields, message_invalid = check_format(config["APP_STRICT"])
        if not config["APP_STRICT"] or not message_invalid:
            with st.spinner(text="generating Data-Matrix-Code ..."):
                dmc = DataMatrixCode(
                    data={FORMAT_ANSI_MH_10: message_fields},
                    use_message_envelope=st.session_state.use_message_envelope,
                    use_format_envelope=st.session_state.use_format_envelope,
                    n_quiet_zone_modules=st.session_state.n_quiet_zone_modules,
                    rectangular_dmc=st.session_state.use_rectangular
                )
                dmc.get_message()
                message_string = dmc.get_message()
                n_ascii_characters = dmc.n_ascii_characters
                img = dmc.generate_image()
            # display result
            draw_results(img, message_string, n_ascii_characters)


if __name__ == "__main__":
    # set logging level
    # logging.basicConfig(
    #     level=cast_logging_level(get_env_variable("LOGGING_LEVEL", logging.DEBUG)),
    #     format="%(asctime)s [%(levelname)s] %(message)s",
    #     handlers=[
    #         # logging.FileHandler(Path(get_env_variable("LOGFILE", "log")).with_suffix(".log")),
    #         logging.StreamHandler(sys.stdout)
    #     ],
    # )

    main()
