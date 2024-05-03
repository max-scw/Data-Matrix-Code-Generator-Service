import streamlit as st
import uuid
import binascii
import pandas as pd
import logging

from DataMatrixCode import (
    FORMAT_ANSI_MH_10,
    message_formats,
    DataMatrixCode,
    validate_envelope_format
)
from utils.utils import rstrip_non_ascii_characters
from utils.config import DMCConfig
from utils.utils_streamlit import config_page_head


from typing import Dict, List


# global constants
DI_FORMAT = FORMAT_ANSI_MH_10


@st.cache_data
def get_format_mapping():
    return message_formats(DI_FORMAT).get_di_mapping()


def create_unique_key():
    return int(uuid.uuid4())


def clear_rows(config: DMCConfig):
    st.session_state.rows = [Row(el[0]) for el in config.required_dis] if config.required_dis else [Row()]


class Row:
    def __init__(self, selected_option: str = None) -> None:
        self.key_select_box = create_unique_key()
        self.key_text_box = create_unique_key()
        self.text_input = None
        self.selected_option = selected_option

    def __repr__(self) -> str:
        return f"Row({self.key_select_box}, {self.selected_option}, {self.key_text_box}, {self.text_input}, {self.description})"

    @property
    def description(self) -> str:
        return get_format_mapping()[self.selected_option]["Explanation"] if self.selected_option else None

    @property
    def meta_data(self) -> str:
        return get_format_mapping()[self.selected_option]["Meta Data"]


def create_row(options, row: Row):
    columns = st.columns([1, 3])
    with columns[0]:
        row.selected_option = st.selectbox(
            "Data Identifier:",
            options,
            index=options.index(row.selected_option) if row.selected_option else 0,
            key=row.key_select_box,
            help=row.description
        )
    with columns[1]:
        row.text_input = rstrip_non_ascii_characters(st.text_input(
            "Content:",
            value=row.text_input if row.text_input else "",
            key=row.key_text_box,
            # help=row.meta_data
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


# ----- checks before generating a DMC
def raise_st_message(strict: bool, msg: str, msg_error: str = "", msg_warning: str = ""):
    logging.warning(msg)
    if strict:
        st.error(msg + msg_error, icon="🚨")
    else:
        st.warning(msg + msg_warning, icon="⚠️")

def check_for_duplicate_rows(strict: bool) -> bool:
    ids = [row.selected_option for row in st.session_state.rows if (row.text_input is not None) and (row.text_input != "")]
    if len(ids) != len(set(ids)):
        msg = f"Rows should have unique data identifiers."

        raise_st_message(strict, msg, " No Code generated.", " Duplicated entries are ignored.")
        return False
    return True


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
                      f"specifications: {get_format_mapping()[data_identifier]['Meta Data']}."
                raise_st_message(strict, msg)
            else:
                message_fields[data_identifier] = content

            invalid |= not flag_valid

    return message_fields, invalid


def check_required_data_identifiers(data_identifiers: List[str], config: DMCConfig) -> bool:
    print(config.required_dis)
    # initialize return variable
    all_found = True
    # walk through required data identifiers
    for dis in config.required_dis:
        was_found = False
        for di in dis:
            if di in data_identifiers:
                was_found = True
                break

        if not was_found:
            msg = f"Data Identifier{'s' if len(dis) > 1 else ''} {' or '.join(dis)} required but missing. Please add a row with it."
            raise_st_message(config["APP_STRICT"], msg)
            all_found = False
    return all_found


# ---- Config
def initialize_options(config: DMCConfig):
    # default values
    if "use_message_envelope" not in st.session_state:
        st.session_state.use_message_envelope = config["DMC_USE_MESSAGE_ENVELOPE"]

    if "use_format_envelope" not in st.session_state:
        st.session_state.use_format_envelope = config["DMC_USE_FORMAT_ENVELOPE"]

    if "use_rectangular" not in st.session_state:
        st.session_state.use_rectangular = config["DMC_RECTANGULAR_CODE"]

    if "n_quiet_zone_modules" not in st.session_state:
        st.session_state.n_quiet_zone_modules = config["DMC_NUMBER_QUIET_ZONE_MODULES"]

    if "options_expanded" not in st.session_state:
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
        with tabs[1]:
            encodings = {enc: str(message_string.encode(encoding=enc)) for enc in ["utf-8", "unicode-escape"]}
            encodings["hex"] = binascii.hexlify(message_string.encode(encoding="utf-8"))
            encodings["base64"] = binascii.b2a_base64(message_string.encode(encoding="utf-8"))

            st.write("Message string encodings:")
            for enc, string in encodings.items():
                st.write(f"**{enc}:**")
                st.code(string)

    with columns[1]:
        st.metric("#ASCII characters", n_ascii_characters)


# ----- App
def main():
    config = config_page_head("DMC Generator", page_icon="💡")

    initialize_options(config)

    # Initialize a list to store the dropdown options
    options = list(get_format_mapping().keys())

    if "rows" not in st.session_state:
        clear_rows(config)

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
            )

    draw_rows(options, placeholder, add)

    draw_options()

    # for row in st.session_state.rows:  # FIXME: for debugging only
    #     logging.debug(row)
    # logging.debug("___")

    if generate_dmc:
        # check code
        message_fields, message_invalid = check_format(config["APP_STRICT"])
        required_dis = check_required_data_identifiers(message_fields.keys(), config)

        if not message_invalid and required_dis:
            # check code
            no_duplicates = check_for_duplicate_rows(config["APP_STRICT"])

            if not config["APP_STRICT"] or no_duplicates:
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
