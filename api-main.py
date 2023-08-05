import datetime
import os
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from prometheus_fastapi_instrumentator import Instrumentator

from starlette.background import BackgroundTask
# import uvicorn

from DataMatrixCode import generate_dmc, generate_dmc_from_string, parse_dmc, MessageData, FORMAT_ANSI_MH_10

from typing import Union, Dict

import logging


app = FastAPI()
IMAGE_FOLDER = Path("images")
IMAGE_FOLDER.mkdir(parents=True, exist_ok=True)
app.mount('/images', StaticFiles(directory=IMAGE_FOLDER), name='static')
list_of_temp_files = []
MAX_NUM_TEMP_FILES = 50
DI_FORMAT = FORMAT_ANSI_MH_10

FROM_JSON = "/from-json"
FROM_TEXT = "/from-text"

ENTRYPOINT_DMC_GENERATOR_API = '/generate'
ENTRYPOINT_DMC_GENERATOR_API_MESSAGE = "/message" # TODO
ENTRYPOINT_DMC_GENERATOR_API_MESSAGE_FROM_JSON = ENTRYPOINT_DMC_GENERATOR_API_MESSAGE + FROM_JSON # TODO
ENTRYPOINT_DMC_GENERATOR_API_IMAGE = "/image"
ENTRYPOINT_DMC_GENERATOR_API_IMAGE_FROM_TEXT = ENTRYPOINT_DMC_GENERATOR_API_IMAGE + FROM_TEXT
ENTRYPOINT_DMC_GENERATOR_API_IMAGE_FROM_JSON = ENTRYPOINT_DMC_GENERATOR_API_IMAGE + FROM_JSON
ENTRYPOINT_DMC_GENERATOR_API_COUNT = '/count-ascii-characters' # TODO
ENTRYPOINT_DMC_GENERATOR_API_COUNT_FROM_TEXT = ENTRYPOINT_DMC_GENERATOR_API_COUNT + FROM_TEXT # TODO
ENTRYPOINT_DMC_GENERATOR_API_COUNT_FROM_JSON = ENTRYPOINT_DMC_GENERATOR_API_COUNT + FROM_JSON # TODO

ENTRYPOINT_DMC_GENERATOR_API_PARSER = '/parser'


# create endpoint for prometheus: /metrics
Instrumentator().instrument(app).expose(app)

# ----- Program info
INFO = {
    "Message": f'This is a minimal web-service to generate data-matrix-codes or '
               f'process a message string (presumably from a data-code) to extract '
               f'the field identifiers according to {DI_FORMAT} format.',
    "docs": "/docs (automatic docs with Swagger UI)",
    'Software': 'fastAPI',
    'Startup date': datetime.datetime.now()
}


# ----- helper functions
@app.on_event('shutdown')
def delete_all_temp_files():
    print('shutting down...')
    for i, fl in enumerate(list_of_temp_files):
        print(len(list_of_temp_files) - i)
        cleanup(Path(fl).as_posix())


def cleanup(temp_file: Union[str, Path]):
    # remove file
    Path(temp_file).unlink()


def limit_temp_files():
    while len(list_of_temp_files) > MAX_NUM_TEMP_FILES:
        cleanup(list_of_temp_files.pop(0))


# ----- home
@app.get('/')
async def home():
    return INFO


# ----- API: head
@app.get(ENTRYPOINT_DMC_GENERATOR_API)
async def home_generator():
    return INFO


def dmc_as_fileresponse(data: MessageData, **kwargs):
    """wrapper to return a FileResponse"""

    try:
        if isinstance(data, str):
            img_path = generate_dmc_from_string(data, file_path=IMAGE_FOLDER, **kwargs)
        else:
            img_path = generate_dmc(data, file_path=IMAGE_FOLDER)
    except Exception as ex:
        detail = ex.message if hasattr(ex, 'message') else f"{type(ex).__name__}: {ex}"
        raise HTTPException(status_code=400, detail=detail)

    return FileResponse(img_path,
                        media_type='image/png',
                        background=BackgroundTask(cleanup, temp_file=img_path.as_posix())
                        )


RETURN_HEAD_GENERATOR = """HTTP/1.1 200 OK
Content-Type: image/png; charset=UTF-8
"""

RETURN_OPTIONS_GENERATOR = """HTTP/1.1 200 OK
Allow: GET, POST, HEAD, OPTIONS
Content-Type: images/png; charset=UTF-8
"""


# ----- API: single message string
@app.get(ENTRYPOINT_DMC_GENERATOR_API_IMAGE_FROM_TEXT)
async def generate_dmc_from_text(
    text: str, 
    rectangular_dmc: bool = False, 
    n_quiet_zone_moduls: int = 2,
    ):  # -> FileResponse
    
    return dmc_as_fileresponse(data=text, rectangular_dmc=rectangular_dmc, n_quiet_zone_moduls=n_quiet_zone_moduls,)



# ----- API: from JSON object
# @app.head(ENTRYPOINT_DMC_GENERATOR_API_JSON)
# async def generate_dmc_api_json_head():
#     return """HTTP/1.1 200 OK
# Content-Type: image/png; charset=UTF-8
# """
#
#
# @app.options(ENTRYPOINT_DMC_GENERATOR_API_JSON)
# async def generate_dmc_api_json_options():
#     return """HTTP/1.1 200 OK
# Allow: GET, HEAD, OPTIONS
# Content-Type: images/png; charset=UTF-8
# """


@app.post(ENTRYPOINT_DMC_GENERATOR_API_IMAGE_FROM_JSON)
async def generate_dmc_from_json(data: MessageData) -> FileResponse:
    if not data:
        raise HTTPException(status_code=400, detail="Input data cannot be empty.")

    return dmc_as_fileresponse(data)


# @app.head(ENTRYPOINT_DMC_GENERATOR_API_JSON)
# async def generate_dmc_api_fields_head():
#     return RETURN_HEAD_GENERATOR
#
#
# @app.options(ENTRYPOINT_DMC_GENERATOR_API_JSON)
# async def generate_dmc_api_fields_options():
#     return RETURN_OPTIONS_GENERATOR


# ----- API: message parser
@app.get(ENTRYPOINT_DMC_GENERATOR_API_PARSER)
async def parse_message_to_json(text: str, check_format: bool = True) -> dict:
    try:
        messages = parse_dmc(text, check_format=check_format)
    except Exception as ex:
        detail = ex.message if hasattr(ex, 'message') else f"{type(ex).__name__}: {ex}"
        raise HTTPException(status_code=400, detail=detail)

    # logging
    msg = f"{ENTRYPOINT_DMC_GENERATOR_API_PARSER}: messages={messages}"
    logging.info(msg)

    return messages


if __name__ == '__main__':
    filename_log = os.environ["LOGFILE"] if "LOGFILE" in os.environ else "log"
    #
    # log_file = (Path("Log") / filename_log).with_suffix(".log")
    # if not log_file.parent.exists():
    #     log_file.parent.mkdir()
    # logging.basicConfig(filename=log_file, encoding='utf-8', level=logging.INFO,
    #                     format="%(asctime)s - %(levelname)s: %(message)s")
    #
    # logging.info(f"\n\n\n---------- Start logging. ----------")
    #
    # uvicorn.run(app=app)
    #
    # logging.info(f"---------- done. ----------")

