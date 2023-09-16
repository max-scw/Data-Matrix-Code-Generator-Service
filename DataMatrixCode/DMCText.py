import re

from .utils import (
    validate_format,
    FORMAT_ANSI_MH_10,
    message_formats
    )

from datetime import datetime
from typing import List, Union, Dict, Any


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
        pattern = self._build_envelope_pattern(message_formats().get_message_envelope())

        m = re.match(pattern, self.text)
        if not m:
            raise ValueError(f"No message envelope found in {self.text}. "
                             f"(A message envelope is required according to ISO / IEC 15434.)")
        else:
            # strip envelop characters from text
            return self._strip_envelope_characters(message_formats().get_message_envelope(), m.group())

    def get_content_of_format_envelopes(self) -> Union[Dict[str, List[str]], str]:
        # extract format
        content = dict()
        for nm, fmt in message_formats().get_formats():
            # build envelope
            pattern = self._build_envelope_pattern(fmt)

            m = re.findall(pattern, self.text)
            if m:
                # strip envelop characters from text
                content[fmt] = [self._strip_envelope_characters(fmt, el) for el in m]
        return content

    def get_content(self, split_fields: bool = True, default_format: str = FORMAT_ANSI_MH_10) -> Dict[str, List[str]]:
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
            sep = re.escape(message_formats(fmt).get_envelope()["sep"])
            # split content
            info[fmt] = re.split(sep, val)
        return info


def easy_datetime_format_converter(simplified_format: str) -> str:
    mapping = {
        "YYYY": "%Y",  # Year with century as a decimal number.
        "YY": "%y",  # Year without century as a zero-padded decimal number.
        # "Y": "",  
        "MM": "%m",  # Month as a zero-padded decimal number.
        "MMM": "%b",  # Month as locale’s abbreviated name.
        "DDD": "%a",  # Weekday as locale’s abbreviated name. (TODO: ensure EN)
        "DD": "%d",  # Day of the month as a zero-padded decimal number.
        "hh": "%H",  # Hour (24-hour clock) as a zero-padded decimal number.
        "mm": "%M",  # Minute as a zero-padded decimal number.
        "ss": "%S",  # Second as a zero-padded decimal number.
        "ff": "%f",  # Microsecond as a decimal number, zero-padded to 6 digits.
        "WW": "%W",  # Week number of the year (Monday as the first day of the week) as a zero-padded decimal number. All days in a new year preceding the first Monday are considered to be in week 0.
        "TTTT": "%H%M"  #??? 22D Record Date Time Stamp (YYYYMMDDTTTT) where T equals hour and minutes
        }
    # locale.setlocale(locale.LC_TIME, "en_US")

    datetime_format = ""
    for el in split_repeating_elements(simplified_format):
        if el in mapping:
            datetime_format += mapping[el]
        else:
            raise Exception(f"Format element {el} unknown.")
    return datetime_format


def split_repeating_elements(string: str) -> List[str]:
    sections = []

    if len(string) > 1:
        sct = string[0]
        for el in string[1:]:
            if el in sct:
                sct += el
            else:
                sections.append(sct)
                sct = el
        sections.append(sct)
    return sections


def get_date_format(explanation: str):        
    # regex pattern
    pattern = r"(?<=[\s\(\[])[YMDHTymdhsfpo\[\]]{4,23}(?=[\s\)\]\.])"
    return re.search(pattern, explanation)


class FormatParser:
    def __init__(self, di_format: str, fields: List[str], strict: bool = True, verbose: bool = False) -> None:
        msg_formats = message_formats(di_format)
        self.di_format = msg_formats.di_format
        self.di_mapping = msg_formats.get_di_mapping()
        self.di_pattern = msg_formats.get_di_pattern()

        self.fields = fields
        self.strict = strict
        self.verbose = verbose

    def check_text(self, di: str, text: str, cast: bool = True) -> (bool, Union[str, int]):
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
        if di[-1] == "D":  # datetime
            # extract date format from explanation
            explanation = self.di_mapping[di]["Explanation"]
            m = get_date_format(explanation)
            if m:
                # get format
                datetime_format = m.group()
                # text = self.__to_datetime_by_format(text, datetime_format)
                text = datetime.strptime(text, easy_datetime_format_converter(datetime_format))
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
        print(f"DEBUG FormatParser.__to_datetime_by_format(): date_info={date_info}, datetime_format={datetime_format}")
        
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
                text_ogl = str(m.string[m.end():])
                # check if the text meets the specified format
                valid_code_id, text = self.check_text(di, text_ogl, cast=cast)
                # update overall flag for valid code
                valid_code_overall = valid_code_overall and valid_code_id
                # info.append((di, text, valid_code_id))
                element = {"data_identifier": di, "content": text, "code_valid": valid_code_id, "string": text_ogl}
                print(f"DEBUG FormatParser.parse(): element={element}")
                info.append(element)
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


def put_into_message_envelope(message: str) -> str:
    return message_formats().get_message_envelope("head") + message + message_formats().get_message_envelope("tail")


class DMCMessageBuilder:
    __dmc_string = None

    def __init__(
            self,
            message_fields: Union[Dict[str, Any], List[str], List[str], str] = None,
            message_format: str = FORMAT_ANSI_MH_10
            ) -> None:
        self.message_format = message_formats(message_format)
        self.message = self._join_message_fields(message_fields) if message_fields else ""

    @property
    def data_identifiers(self) -> List[str]:
        return list(self.message_format.get_di_mapping().keys())

    @property
    def fmt_head(self) -> str:
        return self.message_format.get_envelope("head")

    @property
    def fmt_tail(self) -> str:
        return self.message_format.get_envelope("tail")

    @property
    def fmt_sep(self) -> str:
        return self.message_format.get_envelope("sep")

    def _join_message_fields(self, message_fields) -> str:
        if isinstance(message_fields, dict):
            message = []
            for ky, val in message_fields.items():
                if isinstance(val, datetime):
                    assert ky[-1] == "D", f"Data identifeir '{ky}' is no date identifier."
                    # get explanation
                    explanation = self.message_format.get_di_mapping()[ky]["Explanation"]
                    # extract format from explanation
                    m = get_date_format(explanation)
                    if m:
                        simplified_format = m.group()
                    else:
                        raise Exception(f"Could not extract a date format from the explanation of '{ky}'.")
                    datetime_format = easy_datetime_format_converter(simplified_format)
                    val = val.strftime(format=datetime_format)
                message.append(f"{ky}{val}" )
        return self.fmt_sep.join(message)

    def put_into_format_envelope(self) -> str:
        message = self.fmt_head + self.message + self.fmt_tail
        return message

    def build_message_string(self,
                             use_format_envelope: bool = False,
                             use_message_envelope: bool = True
                             ) -> str:
        if use_format_envelope:
            self.message = self.put_into_format_envelope()
        if use_message_envelope:
            dmc_string = put_into_message_envelope(self.message)
        else:
            dmc_string = self.message

        if not dmc_string.isascii():
            raise Warning(f"String '{dmc_string}' is not a pure ASCII string.")

        self.__dmc_string = dmc_string
        return self.__dmc_string
    
    def get_message_string(self, **kwargs) -> str:
        if self.__dmc_string is None:
            self.build_message_string(**kwargs)
        
        return self.__dmc_string
    
    @property
    def n_ascii_characters(self) -> int:
        return count_compressed_ascii_characters(self.get_message_string())


def count_compressed_ascii_characters(msg: str) -> int:
    n = 0
    last_char_was_reduced = False
    for i in range(len(msg)):
        if not last_char_was_reduced and (msg[i].isnumeric() and msg[i - 1].isnumeric()):
            last_char_was_reduced = True
        else:
            n += 1
            last_char_was_reduced = False
    return n


if __name__ == "__main__":
    dmc_text = "[)>\x1eS123456\x1dV123H48999\x1d18D202312011155\x1d15D24121990\x1dD230501\x04"

    DMCMessageParser(dmc_text).get_content_of_message_envelope()
    tmp = DMCMessageParser(dmc_text).get_content(default_format=FORMAT_ANSI_MH_10)

    # input
    di_format_in = FORMAT_ANSI_MH_10
    fields_in = tmp[di_format_in] + ["D_____________________________________"]

    segments, flag_valid = FormatParser(di_format_in, fields_in, strict=False, verbose=True).parse(True)
    print(segments)

    message_string = DMCMessageBuilder(message_fields="TEST").get_message_string()