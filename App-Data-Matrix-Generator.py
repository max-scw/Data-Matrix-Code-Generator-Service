from datetime import datetime

import streamlit as st
import uuid
import binascii

from typing import Dict, Union

from DMCGenerator import DMCGenerator
from DMCText import DMCMessageBuilder, FormatParser, DATA_IDENTIFIERS

DI_FORMAT = "ANSI-MH-10"
FORMAT_MAPPING = DATA_IDENTIFIERS[DI_FORMAT]["mapping"]


def create_unique_key():
    return int(uuid.uuid4())


def clear_fields():
    del st.session_state.fields


def create_new_row(di: str = "") -> Dict[str, Union[str, int]]:
    return {"di": di, "content": "", "keys": [create_unique_key() for _ in range(3)]}


def draw_input_rows():
    # default values
    if "fields" not in st.session_state:
        st.session_state.fields = [create_new_row()]

    # draw row(s)
    for i, fld in enumerate(st.session_state.fields):
        placeholder = st.empty()
        col1, buff, col2 = st.columns([1, 1, 4])
        with col1:
            di = st.selectbox("Data Identifier", DMCMessageBuilder().data_identifiers, key=fld["keys"][0],
                              # on_change=,
                              )
            print(f"DEBUG: di={di}")
            draw_info(di if di != fld["di"] else None, placeholder)
            fld["di"] = di

        with col2:
            fld["content"] = st.text_input("Content", key=fld["keys"][1])  # placeholder=fld["content"],

            # TODO: check code on change
            # di = fld["di"]
            value = fld["content"]
            if value:
                segments, flag_valid = FormatParser(DI_FORMAT, [di + value],
                                                    strict=False, verbose=False).parse()
                if not flag_valid:
                    st.warning(f"The value '{value}' for data identifier '{di}' does not comply with the format "
                               f"specifications: {FORMAT_MAPPING[di]['Meta Data']}.", icon="⚠️")

def draw_info(di: str, placeholder):
    if di:
        with placeholder:
            st.info(FORMAT_MAPPING[di]["Explanation"], icon="ℹ️")

def add_new_row():
    print(f"DEBUG: st.session_state.fields={st.session_state.fields}")
    # delete empty rows
    st.session_state.fields = [fld for fld in st.session_state.fields if fld["content"] != ""]

    flag_add_new_row = True
    data_identifiers = [row["di"] for row in st.session_state.fields]
    for di in list(set(data_identifiers)):  # convert to set to get a unique list
        if data_identifiers.count(di) > 1:
            st.error(f"The data identifier '{di}' is already defined.", icon="🚨")  # chr(int("U+1F6A8"[2:], 16))
            flag_add_new_row = False

    if flag_add_new_row:
        # add to session space
        st.session_state.fields.append(create_new_row())
        st.experimental_rerun()


def draw_options():
    # default values
    if "use_message_envelope" not in st.session_state:
        st.session_state.use_message_envelope = True

    if "use_format_envelope" not in st.session_state:
        st.session_state.use_format_envelope = False

    if "use_rectangular" not in st.session_state:
        st.session_state.use_rectangular = False

    if "n_quiet_zone_moduls" not in st.session_state:
        st.session_state.n_quiet_zone_moduls = 2

    if "options_expanded" not in st.session_state:
        st.session_state.options_expanded = False

    # options container
    with st.expander("Options", expanded=st.session_state.options_expanded):
        columns = st.columns([1, 1], gap="large")
        with columns[0]:
            st.markdown("*Message string options*")
            st.session_state.use_message_envelope = st.checkbox("message envelope",
                                                                value=st.session_state.use_message_envelope,
                                                                key=None,
                                                                help=None
                                                                )
            st.session_state.use_format_envelope = st.checkbox("format envelope",
                                                               value=st.session_state.use_format_envelope,
                                                               key=None,
                                                               help=None
                                                               )
        with columns[1]:
            st.markdown("*Data-Matrix-Code generator options*")
            st.session_state.use_rectangular = st.checkbox("rectangular DMC",
                                                           value=st.session_state.use_rectangular,
                                                           help="Should a rectangular DMC be generated?"
                                                           )
            st.session_state.n_quiet_zone_moduls = st.number_input(r"\# moduls for quiet zone",
                                                                   label_visibility="visible",
                                                                   min_value=0,
                                                                   max_value=10,
                                                                   value=st.session_state.n_quiet_zone_moduls,
                                                                   help="Number of empty (white) moduls that frame the DMC",
                                                                   )


def main():
    # configure page => set favicon and page title
    st.set_page_config(page_title="DMC Generator", page_icon="💡")  #  chr(int(" U+1F4A1"[2:], 16)) # https://emojipedia.org/  chr(int("U+1F6A8"[2:], 16))
    st.title("Data-Matrix-Code Service")

    draw_input_rows()

    # add buttons
    columns = st.columns([1, 1, 3, 1], gap="small")
    with columns[0]:
        add = st.button(label="add", type="secondary", use_container_width=True)
    with columns[1]:
        st.button(label="clear", type="secondary", on_click=clear_fields, use_container_width=True)
    with columns[3]:
        generate_dmc = st.button(label="generate", type="primary", use_container_width=True)

    # add new row
    if add:
        add_new_row()

    draw_options()
    # placeholder = st.empty()

    message_fields = {fld["di"]: fld["content"] for fld in st.session_state.fields}
    message_string = DMCMessageBuilder(message_fields, DI_FORMAT).get_message_string(
        use_message_envelope=st.session_state.use_message_envelope,
        use_format_envelope=st.session_state.use_format_envelope
    )

    if generate_dmc:
        with st.spinner(text="generating Data-Matrix-Code ..."):
            dmc_generator = DMCGenerator(message_string)
            img = dmc_generator.generate(
                n_quiet_zone_moduls=st.session_state.n_quiet_zone_moduls,
                use_rectangular=st.session_state.use_rectangular
            )
            n_ascii_characters = dmc_generator.n_compressed_ascii_chars


        # with st.empty():
        #     st.success('Done!', icon="✅")

        columns = st.columns([5, 1], gap="small")

        with columns[0]:
            tabs = st.tabs(["Image", "Message String"])
            with tabs[0]:
                st.image(img, caption=message_string)
            with tabs[1]:
                # st.table({enc: str(message_string.encode(encoding=enc)) for enc in ["UTF-8", "unicode-escape"]})
                encodings = {"backslash-replace": message_string.encode("utf-8", "backslashreplace").decode("utf-8", "backslashreplace"),
                             "XML char reference replace": message_string.encode("utf-8", "xmlcharrefreplace").decode("utf-8",
                                                                                                                   "xmlcharrefreplace"),
                             "named replace": message_string.encode("utf-8", "namereplace").decode("utf-8", "namereplace"),
                             "hex": binascii.hexlify(message_string.encode("utf-8")),
                             "base64": binascii.b2a_base64(message_string.encode("utf-8")),
                             "ord": [ord(el) for el in message_string]
                             }
                for enc, string in encodings.items():
                    st.write(f"encoding: {enc}")
                    st.write(string)

        with columns[1]:
            st.metric("#ASCII characters", n_ascii_characters)


if __name__ == "__main__":
    main()
 # streamlit run App.py
