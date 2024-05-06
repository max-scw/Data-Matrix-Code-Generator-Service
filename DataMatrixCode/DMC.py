from .utils import MessageData, message_data_to_list, EnvelopeData

from .DMCText import (
    DMCMessageParser, 
    FormatParser, 
    DMCMessageBuilder, 
    put_into_message_envelope, 
    count_compressed_ascii_characters
)
from .DMCGenerator import generate_dmc_from_string

from typing import Union, Dict, List
from pathlib import Path
from PIL import Image


class DataMatrixCode:
    __dmc_string = None

    def __init__(self, 
                 data: Union[List[dict], dict], 
                 use_format_envelope: bool, 
                 use_message_envelope: bool,
                 **kwargs
                 ) -> None:
        self.use_format_envelope = use_format_envelope
        self.use_message_envelope = use_message_envelope
        self._kwargs = kwargs
        # TODO: format!
        self.data = data if isinstance(data, list) else [data]

    @staticmethod
    def _process_messages(data: List[dict]) -> dict:
        # merge contents if necessary
        envelopes = dict()
        for env in data:
            for fmt, flds in env.items():
                if fmt in data:
                    for ky, val in flds:
                        envelopes[fmt][ky] = val
                else:
                    envelopes[fmt] = flds

        valid_content, _ = validate_envelope_format(envelopes)
        return valid_content

    def get_message(self) -> str:
        if self.__dmc_string is None:
            self.__dmc_string = self.__get_message()
        return self.__dmc_string

    def __get_message(self) -> str:
        envelopes = self._process_messages(self.data)

        # ensure that format envelopes are used if there are more than two (format) envelopes
        self.use_format_envelope |= (len(envelopes) > 1)

        message_string = ""
        for fmt, flds in envelopes.items():
            builder = DMCMessageBuilder(message_fields=flds, message_format=fmt)
            message_string += builder.get_message_string(use_message_envelope=False,
                                                         use_format_envelope=self.use_format_envelope)
        if self.use_message_envelope:
            message_string = put_into_message_envelope(message_string)

        return message_string
    
    @property
    def n_ascii_characters(self) -> int:
        return count_compressed_ascii_characters(self.get_message())

    def generate_image(self):
        content_string = self.get_message()
        return generate_dmc_from_string(
            content_string=content_string,
            **self._kwargs
            )


def validate_envelope_format(
        envelopes: dict,
        do_type_cast: bool = False,
        keep_only_valid_fields: bool = True
) -> (dict, bool):
    def _fields_to_message(fields: dict) -> List[str]:
        return [f"{ky}{val}" for ky, val in fields.items()]

    format_not_valid = False
    valid_envelopes = dict()
    for fmt, flds in envelopes.items():
        if isinstance(flds, dict):
            messages = _fields_to_message(flds)
        elif isinstance(flds, list):
            messages = flds
        else:
            raise ValueError(f"Unexpected input type {type(flds)}.")
        segments, segment_valid = FormatParser(fmt, messages, strict=False, verbose=False).parse(do_type_cast)
        
        format_not_valid |= (not segment_valid)
        # keep only valid envelopes
        if keep_only_valid_fields:
            valid_envelopes[fmt] = {el["data_identifier"]: el["content"] for el in segments if el["code_valid"]}
        else:
            valid_envelopes[fmt] = {el["data_identifier"]: el["content"] for el in segments}

    all_formats_valid = not format_not_valid
    return valid_envelopes, all_formats_valid


def generate_dmc(data: MessageData, file_path: Union[str, Path] = None) -> Union[Image.Image, Path]:
    """wrapper"""
    args = {
        "n_quiet_zone_moduls": data.n_quiet_zone_moduls,
        "rectangular_dmc": data.rectangular_dmc,
        "use_format_envelope": data.use_format_envelope,
        "use_message_envelope": data.use_message_envelope
    }
    if file_path:
        args["file_path"] = file_path

    fields = message_data_to_list(data)
    return DataMatrixCode(data=fields, **args).generate_image()


def generate_message_string(data: MessageData) -> str:
    """wrapper"""
    args = {
        "use_format_envelope": data.use_format_envelope,
        "use_message_envelope": data.use_message_envelope
    }

    fields = message_data_to_list(data)
    return DataMatrixCode(data=fields, **args).get_message()


def parse_dmc(text: str, check_format: bool = True, do_type_cast: bool = False) -> Dict[str, List[str]]:
    content = DMCMessageParser(text).get_content()
    content, _ = validate_envelope_format(content, do_type_cast, check_format)
    return content


if __name__ == "__main__":
    # Example generate_dmc(), a wrapper function to generate a DMC
    info = MessageData(messages=[EnvelopeData(fields={"S": 1234567})])
    img = generate_dmc(info)
    img.show()

    # Example parse_dmc(), a wrapper function to split a message string (of a DMC) into its fields
    text_dmc = "[)>\x1eS123456\x1dV123H48999\x1d18D202312011155\x1d15D24121990\x04"
    parse_dmc(text_dmc)

