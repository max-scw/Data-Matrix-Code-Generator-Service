from pathlib import Path
from typing import Union, Dict

# TODO: wrap to MessageFormat class

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