from pathlib import Path
from typing import Union, Dict, List


FORMAT_ANSI_MH_10 = "ANSI-MH-10"
PATH_TO_DI_FORMATS = {FORMAT_ANSI_MH_10: Path(__file__).parent / "ANSI-MH-10_DataIdentifiers.txt"}


def load_mapping(filename: Union[Path, str]) -> Dict[str, Dict[str, str]]:
    # read file
    with open(filename, "r") as fid:
        lines = fid.readlines()
    # split text in lines
    data = [ln.strip("\n").split(";") for ln in lines if len(ln) > 5]
    assert all([len(el) == 3 for el in data]), "File with data identifiers is not correctly formatted. Expected were 3 entries per line."

    # get rid of description:
    description = data.pop(0)

    # reorganize data
    mapping = dict()
    for el in data:
        meta_data, data_identifier, explanation = el
        mapping[data_identifier] = {"Meta Data": meta_data, "Explanation": explanation}
    return mapping


# ---------- FORMAT SPECIFICATIONS
# | ASCII | unicode | html | hex | escape sequence | description
# | --- | --- | --- | --- | --- | ---
# | EOT | U+0004 | &#4;  | \x04 | ^D | End Of Transmission
# | GS  | U+001D | &#29; | \x1d | ^] | Group Separator
# | RS  | U+001E | &#30; | \x1e | ^^ | Record Separator
MESSAGE_ENVELOPE = {"head": "\u005B\u0029\u003E\u001E", "tail": "\u0004"}

FORMAT_ENVELOPES = {FORMAT_ANSI_MH_10: {"head": "06\u001D", "tail": "\u001e", "sep": "\u001D"}}
DATA_IDENTIFIERS = {FORMAT_ANSI_MH_10: {"pattern": r"\d{0,2}[B-Z]",
                                        "mapping": load_mapping(PATH_TO_DI_FORMATS[FORMAT_ANSI_MH_10])}}

# ---- wrappers
def _get_envelope(envelope: dict, key: str = None) -> Union[str, Dict[str, str]]:
    if key:
        if key in envelope:
            return envelope[key]
        else:
            raise ValueError(f"Unknown key '{key}' for format evelope. Available keys are: {list(envelope.keys())}")
    else:
        return envelope
    
    
class message_formats:
    def __init__(self, di_format: str = None) -> None:
        if di_format:
            self.set_format(di_format)
    
    @staticmethod
    def get_formats() -> List[str]:
        return list(FORMAT_ENVELOPES.keys())
    
    @staticmethod
    def get_message_envelope(key: str = None) -> Dict[str, str]:
        return _get_envelope(MESSAGE_ENVELOPE, key)
    
    # --- Data Identifier specific methods
    def set_format(self, di_format: str) -> bool:
        if di_format not in DATA_IDENTIFIERS:
            raise ValueError(f"Format '{di_format}' not found. Available formats are: {self.get_formats()}")
        self._di_format = di_format
        return True
    
    @property
    def di_format(self) -> str:
        if self._di_format:
            return self._di_format
        else:
            raise Exception(f"No Data Identifier format (di_format) has been set yet!")

    def get_di_mapping(self) -> Dict[str, Dict[str, str]]:
        return DATA_IDENTIFIERS[self.di_format]["mapping"]
    
    def get_di_pattern(self) -> str:
        return DATA_IDENTIFIERS[self.di_format]["pattern"]
    
    def get_envelope(self, key: str = None) -> Union[str, Dict[str, str]]:
        return _get_envelope(FORMAT_ENVELOPES[self.di_format], key)
    







