from .utils import MessageData, message_data_to_list, EnvelopeData

from .DMCText import DMCMessageParser, FormatParser, DMCMessageBuilder, put_into_message_envelope
from .DMCGenerator import DMCGenerator

from typing import Union, Dict, List
from pathlib import Path
from PIL import Image


class DMC:
    def __init__(self, data: Union[List[dict], dict], use_format_envelope: bool, **kwargs):
        self.use_format_envelope = use_format_envelope
        self._kwargs = kwargs

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

        return validate_format(envelopes)

    def get_message(self) -> str:
        envelopes = self._process_messages(self.data)

        # ensure that format envelopes are used if there are more than two (format) envelopes
        self.use_format_envelope |= (len(envelopes) > 1)

        message_string = ""
        for fmt, flds in envelopes.items():
            builder = DMCMessageBuilder(message_fields=flds, message_format=fmt)
            message_string += builder.get_message_string(use_message_envelope=False,
                                                         use_format_envelope=self.use_format_envelope)

        content_string = put_into_message_envelope(message_string)
        return content_string

    def generate_image(self):
        content_string = self.get_message()
        return DMCGenerator(content_string).generate(**self._kwargs)


def validate_format(envelopes: dict) -> dict:

    def _fields_to_message(fields: dict) -> List[str]:
        return [f"{ky}{val}" for ky, val in fields.items()]

    valid_envelopes = dict()
    for fmt, flds in envelopes.items():
        if isinstance(flds, dict):
            messages = _fields_to_message(flds)
        elif isinstance(flds, list):
            messages = flds
        else:
            raise ValueError
        segments, segment_valid = FormatParser(fmt, messages, strict=False, verbose=True).parse(True)
        # keep only valid envelopes
        valid_envelopes[fmt] = {el["data_identifier"]: el["content"] for el in segments if el["code_valid"]}

    return valid_envelopes


def generate_dmc(data: MessageData, file_path: Union[str, Path] = None) -> Union[Image.Image, Path]:
    """wrapper"""
    args = {
        "n_quiet_zone_moduls": data.n_quiet_zone_moduls,
        "use_rectangular": data.rectangular_dmc,
        "use_format_envelope": data.use_format_envelope
    }
    if file_path:
        args["file_path"] = file_path

    fields = message_data_to_list(data)
    return DMC(data=fields, **args).generate_image()


def parse_dmc(text: str, check_format: bool = True) -> Dict[str, List[str]]:
    content = DMCMessageParser(text).get_content()
    if check_format:
        content = validate_format(content)
    return content


if __name__ == "__main__":
    # Example generate_dmc(), a wrapper function to generate a DMC
    info = MessageData(messages=[EnvelopeData(fields={"S": 1234567})])
    img = generate_dmc(info)
    img.show()

    # Example parse_dmc(), a wrapper function to split a message string (of a DMC) into its fields
    text_dmc = "[)>\x1eS123456\x1dV123H48999\x1d18D202312011155\x1d15D24121990\x04"
    parse_dmc(text_dmc)


