import re

from utils.format_specifications import validate_format

from datetime import datetime
from typing import List, Union, Dict, Tuple, Any


# function required for global initialization
def load_mapping(filename: str) -> Dict[str, Dict[str, str]]:
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
FORMAT_ENVELOPE = {"ANSI-MH-10": {"head": "06\u001D", "tail": "\u001e", "sep": "\u001D"}}
MESSAGE_ENVELOPE = {"head": "\u005B\u0029\u003E\u001E", "tail": "\u0004"}
DATA_IDENTIFIERS = {"ANSI-MH-10": {"pattern": r"\d{0,2}[B-Z]",
                                   "mapping": load_mapping("utils/ANSI-MH-10_DataIdentifiers.txt")}}


class DMCMessageParser:
    def __init__(self, text: str):
        self.text = text  # encode?

    @staticmethod
    def _build_envelope_pattern(env: Dict[str, str]) -> str:
        return re.escape(env["head"]) + ".*" + re.escape(env["tail"])

    @staticmethod
    def _strip_envelope_characters(env: Dict[str, str], text: str) -> str:
        return text[len(env["head"]):-len(env["tail"])]

    def get_content_of_message_envelope(self) -> str:
        # build envelope
        pattern = self._build_envelope_pattern(MESSAGE_ENVELOPE)

        m = re.match(pattern, self.text)
        if not m:
            raise ValueError(f"No message envelope found in {self.text}. "
                             f"(A message envelope is required according to ISO / IEC 15434.)")
        else:
            # strip envelop characters from text
            return self._strip_envelope_characters(MESSAGE_ENVELOPE, m.group())

    def get_content_of_format_envelopes(self) -> Union[Dict[str, List[str]], str]:
        # extract format
        content = dict()
        for nm, fmt in FORMAT_ENVELOPE.items():
            # build envelope
            pattern = self._build_envelope_pattern(fmt)

            m = re.findall(pattern, self.text)
            if m:
                # strip envelop characters from text
                content[fmt] = [self._strip_envelope_characters(fmt, el) for el in m]
        # # default output
        # if content == {}:
        #     return {"None": self.get_content_of_message_envelope()}
        return content

    def get_content(self, split_fields: bool = True, default_format: str = None) -> Dict[str, List[str]]:
        content = self.get_content_of_format_envelopes()
        # add default format if no format envelope is specified
        if content == {}:
            if default_format:
                content = {default_format: self.get_content_of_message_envelope()}
            else:
                raise ValueError(f"No format envelop found in '{self.text}' and no default format specified.")

        if split_fields:
            return self._split_content(content)
        else:
            return content

    @staticmethod
    def _split_content(env: Dict[str, List[str]]) -> Dict[str, List[str]]:
        info = dict()
        for fmt, val in env.items():
            # get separator (as regex pattern)
            sep = re.escape(FORMAT_ENVELOPE[fmt]["sep"])
            # split content
            info[fmt] = re.split(sep, val)
        return info


class FormatParser:
    def __init__(self, di_format: str, fields: List[str], strict: bool = True, verbose: bool = False) -> None:
        if di_format not in DATA_IDENTIFIERS:
            raise ValueError
        self.di_format = di_format
        self.di_mapping = DATA_IDENTIFIERS[di_format]["mapping"]
        self.di_pattern = DATA_IDENTIFIERS[di_format]["pattern"]

        self.fields = fields
        self.strict = strict
        self.verbose = verbose

    def check_text(self, di: str, text: str, cast: bool = True) -> (bool, Union[str, int]):  # TODO: also date time?
        valid_code = True
        # verify di (that exists)
        if di not in self.di_mapping:
            msg = f"Data identifier '{di}' is not a valid identifier for {self.di_format}."
            valid_code = rais_error_or_warning(msg, self.strict, self.verbose)

        # check if there is text at all (use len() in case bytes or similar are handed to the function).
        if len(text) == 0:
            msg = f"Data identifier '{di}' seems to have no content accompanied."
            valid_code = rais_error_or_warning(msg, self.strict, self.verbose)

        # extract meta data from mapping
        meta_data = self.di_mapping[di]["Meta Data"]
        if meta_data != "":
            valid_code = valid_code and validate_format(meta_data, di + text, self.strict)
        else:
            # allow printable ascii characters (33, 126)
            valid_code = valid_code and (True if re.match(r"[ -~]+$", text) else False)

        if cast and valid_code:
            text = self._cast_text(di, text)
        return valid_code, text

    def _cast_text(self, di: str, text: str) -> Union[str, int, float, datetime]:
        if "D" in di:  # datetime
            # search for datetime format in explanations
            explanation = self.di_mapping[di]["Explanation"]
            m = re.search(r"(?<=[\s\(\[])[YMDHymdhsfpo\[\]]{4,23}(?=[\s\)\]\.])", explanation)
            if m:
                # get format
                datetime_format = m.group()
                text = self.__to_datetime_by_format(text, datetime_format)
            else:
                msg = f"No datetime format found in description of data identifier '{di}'."
                rais_error_or_warning(msg, self.strict, self.verbose)
        elif re.match(r"\d+$", text):  # integer
            text = int(text)
        elif re.match(r"\d+(\.\d+)?$", text):  # float
            text = float(text)
        return text

    def __to_datetime_by_format(self, text, datetime_format: str) -> datetime:
        """Convert text to python datetime object based on a simplified pattern like YYYYMMDD or MMHHDDMMYYYY"""
        if datetime_format[0] == "Y":
            idx = range(0, len(datetime_format), 1)
        elif datetime_format[-1] == "Y":
            idx = range(len(datetime_format) - 1, 0, -1)
        else:
            idx = []
            msg = f"Expected the datetime format to start or end with the year ('Y') but was {datetime_format}."
            rais_error_or_warning(msg, self.strict, self.verbose)

        dtf_order = "ymdhmsfp"
        date_info = []
        k = 0
        i_last = idx[0]
        upwards = idx[0] < idx[-1]
        for i in idx:
            if datetime_format[i].lower() != dtf_order[k]:
                # convert
                date_info.append(int(text[i_last:i] if upwards else text[i + 1:i_last + 1]))
                k += 1
                i_last = i
        date_info.append(int(text[i_last:] if upwards else text[:i_last + 1]))

        # to datetime object
        try:
            datetime_object = datetime(*date_info)
        except Exception as me:
            msg = "Conversion to python datetime format failed. " + str(me)
            rais_error_or_warning(msg, self.strict, self.verbose)
        return datetime_object

    def parse(self, cast: bool = False) -> (List[Dict[str, Union[str, int, datetime]]], bool):
        info = []
        # initialize flag
        valid_code_overall = True
        for fld in self.fields:
            # get data identifier
            m = re.match(self.di_pattern, fld)
            if m:
                # extract data identifier and corresponding text
                di = str(m.group())
                text = str(m.string[m.end():])
                # check if the text meets the specified format
                valid_code_id, text = self.check_text(di, text, cast=cast)
                # update overall flag for valid code
                valid_code_overall = valid_code_overall and valid_code_id
                # info.append((di, text, valid_code_id))
                info.append({"data_identifier": di, "content": text, "code_valid": valid_code_id})
            else:
                msg = f"No {self.di_format} data identifier found in '{fld}'. " \
                      f"It was expected that the string starts with the pattern '{self.di_pattern}'."
                valid_code_overall = rais_error_or_warning(msg, self.strict, self.verbose)

        return info, valid_code_overall


def rais_error_or_warning(message: str, strict: bool, verbose: bool) -> bool:
    if strict:
        raise ValueError(message)
    else:
        if verbose:
            raise Warning(message + "Skipping this field.")
    return False


def parse_dmc(message: str) -> Dict[str, Dict[str, Any]]:
    """wrapper function"""
    format_envelopes = DMCMessageParser(message).get_content(default_format="ANSI-MH-10")

    content = dict()
    for fmt, flds in format_envelopes.items():
        segmented_flds, fmt_valid = FormatParser(fmt, flds, strict=False, verbose=True).parse(True)
        content[fmt] = segmented_flds

    return segments


class DMCMessageBuilder:
    dmc_string = None

    def __init__(self,
                 message_fields: Union[Dict[str, Any], List[str], List[str], str] = None,
                 format: str = "ANSI-MH-10"
                 ) -> None:
        self.format = format
        self.message = self._join_message_fields(message_fields) if message_fields else ""

    @property
    def data_identifiers(self) -> List[str]:
        return list(DATA_IDENTIFIERS[self.format]["mapping"].keys())

    @property
    def msg_head(self) -> str:
        return MESSAGE_ENVELOPE["head"]

    @property
    def msg_tail(self) -> str:
        return MESSAGE_ENVELOPE["tail"]

    @property
    def fmt_head(self) -> str:
        return FORMAT_ENVELOPE[self.format]["head"]

    @property
    def fmt_tail(self) -> str:
        return FORMAT_ENVELOPE[self.format]["tail"]

    @property
    def fmt_sep(self) -> str:
        return FORMAT_ENVELOPE[self.format]["sep"]

    def _join_message_fields(self, message_fields) -> str:
        if isinstance(message_fields, dict):
            message_fields = [f"{ky}{val}" for ky, val in message_fields.items()]
        return self.fmt_sep.join(message_fields)

    def put_into_message_envelope(self) -> str:
        message = self.msg_head + self.message + self.msg_tail
        return message

    def put_into_format_envelope(self) -> str:
        message = self.fmt_head + self.message + self.fmt_tail
        return message

    def get_message_string(self,
                           use_format_envelope: bool = False,
                           use_message_envelope: bool = True
                           ) -> str:
        if use_format_envelope:
            self.message = self.put_into_format_envelope()
        if use_message_envelope:
            dmc_string = self.put_into_message_envelope()
        else:
            dmc_string = self.message

        if not dmc_string.isascii():
            raise Warning(f"String '{dmc_string}' is not a pure ASCII string.")

        return dmc_string


if __name__ == "__main__":
    dmc_text = "[)>\x1eS123456\x1dV123H48999\x1d18D202312011155\x1d15D24121990\x04"

    DMCMessageParser(dmc_text).get_content_of_message_envelope()
    tmp = DMCMessageParser(dmc_text).get_content(default_format="ANSI-MH-10")

    # input
    di_format_in = "ANSI-MH-10"
    fields_in = tmp[di_format_in] + ["D_____________________________________"]

    segments, flag_valid = FormatParser(di_format_in, fields_in, strict=False, verbose=True).parse(True)
    print(segments)


