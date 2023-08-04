from pydantic import BaseModel
from typing import Optional, Dict, AnyStr, Union, List
from datetime import datetime

from .formats import FORMAT_ANSI_MH_10


class MessageRaw(BaseModel):
    fields: Dict[str, Union[str, int, float]]


class MessageFormatEnvelope(BaseModel):
    fields: Dict[str, MessageRaw]


# class MessageData(BaseModel):
#     # fields
#     fields: Union[str, MessageRaw, MessageFormatEnvelope]
#     # formatting / appearance / options
#     rectangular_dmc:  Optional[bool] = False
#     n_quiet_zone_moduls: Optional[int] = 2


class EnvelopeData(BaseModel):
    format: Optional[str] = FORMAT_ANSI_MH_10
    fields: Dict[str, Union[str, int, float, datetime]]


class MessageData(BaseModel):
    messages: List[EnvelopeData]
    # formatting / appearance / options
    rectangular_dmc:  Optional[bool] = False
    n_quiet_zone_moduls: Optional[int] = 2
    use_format_envelope:  Optional[bool] = True


def envelope_data_to_dict(data: EnvelopeData) -> dict:
    return {data.format: data.fields}


def message_data_to_list(data: MessageData) -> List[dict]:
    return [envelope_data_to_dict(msg) for msg in data.messages]



