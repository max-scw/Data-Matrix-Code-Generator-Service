import streamlit as st
import uuid
import binascii
from pip._vendor import tomli as tomllib  # standard in Python 3.11
from pathlib import Path
from itertools import chain

from typing import Dict, Union, List, Any

from DMCGenerator import DMCGenerator
from DMCText import DMCMessageBuilder, FormatParser, DATA_IDENTIFIERS

DI_FORMAT = "ANSI-MH-10"
FORMAT_MAPPING = DATA_IDENTIFIERS[DI_FORMAT]["mapping"]


class DMCConfig:
    """
    reads the standard streamlit config and looks for the additional segment [DMC], where configs specific for
    this app is stored in.
    Possible config keys:
    - requiredDataIdentifiers: Array of data identifiers, that must be present in a DMC, e.g. ['P', 'S|T', 'V'],
    whereas '|' signifies an OR, i.e. the data identifier S or T must be present in the code, the identifiers P
    and V required without any other option
    """
    def __init__(self, path_to_file: Union[str, Path]):
        config = self._read_config(path_to_file)
        self.config = config["DMC"] if "DMC" in config else []

    @staticmethod
    def _read_config(path_to_file: Union[str, Path]) -> Union[Dict[str, Any], dict]:
        path_to_file = Path(path_to_file).with_suffix(".toml")
        if not path_to_file.exists():
            UserWarning(f"Config file {path_to_file.as_posix()} does not exist.")
            return dict()
        # read file
        with open(path_to_file, "rb") as fid:
            info = tomllib.load(fid)
        return info

    def required_dis(self, flatten: bool = False) -> Union[List[List[str]], list]:
        key = "requiredDataIdentifiers"
        dis = self.config[key] if key in self.config else []
        if dis:
            dis = [di.split("|") for di in dis]
        if flatten:
            dis = list(chain.from_iterable(dis))
        return dis
        

    def check_for_required_dis(self, data_identifiers: Union[List[str], Dict[str, str]], write_error_msg: bool = True) -> Union[List[List[str]], list]:
        # process input it it is the entire 
        if isinstance(data_identifiers, dict):
            data_identifiers = data_identifiers.keys()
        
        missing_dis = []
        # loop through required data identifiers
        for dis in self.required_dis():
            # check if this (required) identifier is in the messages
            if not any([di in data_identifiers for di in dis]):
                missing_dis.append(dis)
        # raise error message if some required data identifiers are missing
        if missing_dis and write_error_msg:
            msg = ", and ".join([" or ".join(dis)for dis in missing_dis])
            st.error(f"Data identifiers {msg} are required for a valid code. "
                     f"Please add these fields", icon="🚨")
        return missing_dis


@st.cache_data
def get_config() -> DMCConfig:
    path_to_config = Path("config.toml")
    if not path_to_config.exists():
        # standard path to streamlit config file
        path_to_config = Path(".streamlit/config.toml")

    # read config file
    return DMCConfig(path_to_config)


def rstrip_non_ascii_characters(text: str) -> str:
    i = 0
    for el in text[::-1]:
        if el.isascii():
            break
        i += 1
    return text[:-i] if i > 0 else text


def create_unique_key():
    return int(uuid.uuid4())


def clear_fields():
    del st.session_state.rows




def draw_input_rows(config: DMCConfig):
    # initialize
    if "rows" not in st.session_state:
        st.session_state.rows = Row(config)

    # draw row(s)
    for i, fld in enumerate(st.session_state.rows):
        placeholder = st.empty()
        col1, _, col2 = st.columns([1, 1, 4])
        with col1:
            select_options = DMCMessageBuilder().data_identifiers
            idx = 0
            if fld["di"] in select_options:
                idx = select_options.index(fld["di"])
            di = st.selectbox("Data Identifier", select_options,
                              index=idx,
                              key=fld["keys"][0])

            # draw info message on change
            if st.session_state.explain_data_identifiers:
                draw_info(di if di != fld["di"] and fld["di"] != "" else None, placeholder)
            
            fld["di"] = di

        with col2:
            content = st.text_input("Content", key=fld["keys"][1])
            # strip unexpected non-ascii characters at the end and tailing spaces
            content = rstrip_non_ascii_characters(content).rstrip(" ")

            fld["content"] = content

            # check code on change
            if content:
                segments, flag_valid = FormatParser(DI_FORMAT, [di + content],
                                                    strict=False, verbose=False).parse()
                if not flag_valid:
                    st.warning(f"The value '{content}' for data identifier '{di}' does not comply with the format "
                               f"specifications: {FORMAT_MAPPING[di]['Meta Data']}.", icon="⚠️")

def draw_info(di: str, placeholder):
    if di:
        with placeholder:
            st.info(f"**{di}**: {FORMAT_MAPPING[di]['Explanation']}", icon="ℹ️")


class Row:
    def __init__(self, config: DMCConfig):
        # store config
        self.config = config
        # initialize rows
        if config.required_dis():
            self.rows = [self._create_new_row(di[0]) for di in config.required_dis()]
        else:
            self.rows = [self._create_new_row()]

    def __iter__(self) -> Dict[str, Any]:
        for row in self.get_rows():
            yield row

    @staticmethod
    def _create_new_row(di: str = "") -> Dict[str, Union[str, int]]:
        return {"di": di, "content": "", "keys": [create_unique_key() for _ in range(2)]}

    @property
    def isempty(self) -> List[bool]:
        return any([self._isemptyrow(el) for el in self.get_nonempty_rows()])
    
    @staticmethod
    def _isemptyrow(row: Dict[str, Any]) -> bool:
        return row["content"] == "" or row["content"].isspace()

    def get_nonempty_rows(self) -> List[Dict[str, Any]]:
        return [el for el in self.get_rows() if not self._isemptyrow(el) or el["di"] in self.config.required_dis(True)]
    
    @staticmethod
    def _get_data_identifiers(rows: List[Dict[str, Any]]) -> List[str]:
        return [fld["di"] for fld in rows]
    
    @property
    def message_fields(self) -> Dict[str, Any]:
        return {fld["di"]: fld["content"] for fld in self.get_nonempty_rows()}
    
    def add_new_row(self) -> bool:
        # check if any row is empty
        rows = self.get_nonempty_rows()
        self.rows = rows

        lg = [self._isemptyrow(el) for el in rows]
        flag_add_new_row = not any(lg)
        # check if (non-empty) data identifiers are unique
        data_identifiers = self._get_data_identifiers(rows)
        for di in list(set(data_identifiers)):  # convert to set to get a unique list
            if data_identifiers.count(di) > 1:
                st.error(f"The data identifier '{di}' is already defined.", icon="🚨")  # chr(int("U+1F6A8"[2:], 16))
                flag_add_new_row = False

        if flag_add_new_row:
            self.rows.append(self._create_new_row())


        return flag_add_new_row

    def get_rows(self) -> List[Dict[str, Any]]:
        data_identifiers = self._get_data_identifiers(self.rows)
        # check requirements
        missing_dis = self.config.check_for_required_dis(data_identifiers, False)
        
        # append missing data_identifiers to list of rows
        for di in missing_dis:
            self.rows.append(self._create_new_row(di[0]))
        return self.rows
    
    def update(self, idx: int, di: str = None, content: Union[str, int, float] = None) -> bool:
        self.rows[idx]["di"] = di
        self.rows[idx]["content"] = content
        return True
            


def initialize_options():
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

    if "explain_data_identifiers" not in st.session_state:
        st.session_state.explain_data_identifiers = True


def draw_options():
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
            st.markdown("*App options*")
            st.session_state.explain_data_identifiers = st.checkbox("explain Data Identifiers",
                                                                    value=st.session_state.explain_data_identifiers,
                                                                    key=None,
                                                                    help="Shows info message when drop-down menu for *Data Identifier* changes."
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


def draw_results(img, message_string: str, n_ascii_characters: int):
    columns = st.columns([5, 1], gap="small")

    with columns[0]:
        tabs = st.tabs(["Image", "Message String"])
        with tabs[0]:
            st.image(img, caption=message_string)
        with tabs[1]:
            # st.table({enc: str(message_string.encode(encoding=enc)) for enc in ["UTF-8", "unicode-escape"]})
            encodings = {"backslash-replace": message_string.encode("utf-8", "backslashreplace").decode("utf-8",
                                                                                                        "backslashreplace"),
                         "XML char reference replace": message_string.encode("utf-8", "xmlcharrefreplace").decode(
                             "utf-8",
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

def main():
    # configure page => set favicon and page title
    st.set_page_config(page_title="DMC Generator", page_icon="💡")  #  chr(int(" U+1F4A1"[2:], 16)) # https://emojipedia.org/  chr(int("U+1F6A8"[2:], 16))
    st.title("Data-Matrix-Code Service")
    # hide "made with Streamlit" text in footer
    hide_streamlit_style = """
                <style>
                #MainMenu {visibility: hidden;}
                footer {visibility: hidden;}
                </style>
                """
    st.markdown(hide_streamlit_style, unsafe_allow_html=True)

    initialize_options()

    config = get_config()
    draw_input_rows(config)

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
        row_added = st.session_state.rows.add_new_row()
        # if row_added:
        st.experimental_rerun()

    draw_options()

    # if button was pressed
    if generate_dmc:
        rows = st.session_state.rows
        # check if no required field is empty
        print(f"DEBUG: rows.isempty={rows.isempty}")
        if not rows.isempty:
            message_fields = rows.message_fields 
            # generate data-matrix-code
            with st.spinner(text="generating Data-Matrix-Code ..."):
                message_string = DMCMessageBuilder(message_fields, DI_FORMAT).get_message_string(
                    use_message_envelope=st.session_state.use_message_envelope,
                    use_format_envelope=st.session_state.use_format_envelope
                )

                dmc_generator = DMCGenerator(message_string)
                img = dmc_generator.generate(
                    n_quiet_zone_moduls=st.session_state.n_quiet_zone_moduls,
                    use_rectangular=st.session_state.use_rectangular
                )
                n_ascii_characters = dmc_generator.n_compressed_ascii_chars
            # display result
            draw_results(img, message_string, n_ascii_characters)


if __name__ == "__main__":
    main()
    # streamlit run App-Data-Matrix-Generator.py

