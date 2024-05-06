from pathlib import Path
import logging
import sys
from itertools import chain
import re

# import tomllib
from pip._vendor import tomli as tomllib  # standard in Python 3.11


from utils.env_vars import get_env_variable, get_environment_variables, cast_logging_level

from typing import List, Dict, Any, Union


def load_default_config(path_to_config: Union[str, Path]) -> dict:
    with open(Path(path_to_config), "r") as fid:
        config_default = tomllib.load(fid)

    config_default_env = dict()
    for group in config_default:
        for ky, vl in config_default[group].items():
            # variable name
            var_nm = "_".join([group, ky]).upper()
            # nm = "_".join([prefix, var_nm]).upper()
            config_default_env[var_nm] = vl if not (isinstance(vl, str) and vl == "") else None

    return config_default_env


def get_config_from_env_vars(default_prefix: str = "", default_config_file: Union[str, Path] = "./default_config.toml") -> dict:
    # --- load default config
    path_to_default_config = Path(default_config_file)

    if path_to_default_config.is_file():
        config_default = load_default_config(path_to_default_config)
    else:
        config_default = dict()

    # get custom config
    prefix = get_env_variable("PREFIX", default_prefix)
    config_environment_vars = get_environment_variables(rf"{prefix}_" if prefix else "", False)

    # merge configs
    config = config_default | config_environment_vars
    logging.debug(f"get_config_from_env_vars(): {config}")

    # set logging
    logging.basicConfig(
        level=cast_logging_level(get_env_variable("LOGGING_LEVEL", logging.DEBUG)),
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            # logging.FileHandler(Path(get_env_variable("LOGFILE", "log")).with_suffix(".log")),
            logging.StreamHandler(sys.stdout)
        ],
    )
    return config


class DMCConfig:
    """
    reads the standard streamlit config and looks for the additional segment [DMC], where configs specific for
    this app is stored in.
    Possible config keys:
    - requiredDataIdentifiers: Array of data identifiers, that must be present in a DMC, e.g. ['P', 'S|T', 'V'],
    whereas '|' signifies an OR, i.e. the data identifier S or T must be present in the code, the identifiers P
    and V required without any other option
    """

    def __init__(
            self,
            path_to_file: Union[str, Path, None] = None,
            default_config_file: str = "./default_config.toml"
    ):
        # store input
        self.__path_to_file = path_to_file
        self.__default_config_file = Path(default_config_file)

        # load config
        self.config = get_config_from_env_vars(path_to_file, self.__default_config_file)

        msg = f"[DMCConfig.__init__]: self.config={self.config}"
        logging.debug(msg)

        # set required data identifiers:
        self.required_dis = self.get_required_dis()

    def __getitem__(self, key: str):
        if key in self.config:
            return self.config[key]
        else:
            logging.debug(self.config)
            raise ValueError(f"Unknown key '{key}' for configuration and default parameters.")

    def __repr__(self):
        init = []
        if self.__path_to_file:
            init.append(f"path_to_file={self.__path_to_file}")
        init.append(f"default_config_file={self.__default_config_file}")

        call = f"DMCConfig({', '.join(init)})"
        return f"{call}: {self.config}"

    def get_required_dis(self, flatten: bool = False) -> Union[List[List[str]], list]:
        key = "DMC_REQUIRED_DATA_IDENTIFIERS"
        dis = []
        if self.config and key in self.config:
            # check for list
            dis = self.config[key] if (key in self.config) and (self.config[key] is not None) else []

            # pattern data identifier
            pat_di = "([0-9]{0,2}[A-Z])"
            # add optional data identifiers
            pat_opt = rf"({pat_di}(\|{pat_di})*)"
            # make list
            pat_list = re.compile(rf"\[{pat_opt}(,\s?{pat_opt})*\]$")

            if isinstance(dis, str) and pat_list.match(dis):
                dis = re.split(r",\s?", dis[1:-1])

            if isinstance(dis, str):
                dis = dis.split("|")
            elif isinstance(dis, list):
                dis = [di.split("|") for di in dis]

            if flatten:
                dis = list(chain.from_iterable(dis))
        return dis

    def check_for_required_dis(
            self,
            data_identifiers: Union[List[str], Dict[str, str]]
    ) -> Union[List[List[str]], list]:
        # process input if it is the entire
        if isinstance(data_identifiers, dict):
            data_identifiers = data_identifiers.keys()

        missing_dis = []
        # loop through required data identifiers
        for dis in self.required_dis:
            # check if this (required) identifier is in the messages
            if not any([di in data_identifiers for di in dis]):
                missing_dis.append(dis)
        return missing_dis

    def isrequireddi(self, data_identifier: str) -> list:
        for dis in self.required_dis:
            if data_identifier in dis:
                return dis
        return []
