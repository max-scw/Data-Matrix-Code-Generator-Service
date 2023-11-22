import os
import re

from pip._vendor import tomli as tomli_r  # standard in Python 3.11
import tomli_w
from pathlib import Path
from itertools import chain

from typing import List, Dict, Any, Union


def camel_case_split(identifier):
    matches = re.finditer(".+?(?:(?<=[a-z])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])|$)", identifier)
    return [m.group(0) for m in matches]


# regex patterns
re_double_quotes = re.compile('\".*\"$')
re_single_quotes = re.compile("'.*'$")
re_list = re.compile("\[.+\]")


def get_environment_variables(camel_case_keys: List[str], prefix: str) -> Dict[str, Any]:

    environment_config = dict()
    for ky in camel_case_keys:
        # build name of environment variable
        name = (f"{prefix}_" + "_".join(camel_case_split(ky))).upper()
        val = os.environ.get(name)
        if val is not None:
            # strip quotation marks
            if re_double_quotes.match(val) or re_single_quotes.match(val):
                val = val[1:-1]
            # check if it is a list
            if re_list.match(val):
                val = val[1:-1].replace(" ", "").split(",")

            # type cast
            environment_config[ky] = [cast(el.strip("'").strip('"')) for el in val] if isinstance(val, list)  else cast(val)
    return environment_config


def cast(var: str) -> Union[None, int, float, str, bool]:
    """casting strings to primitive datatypes"""
    if re.match(r"[0-9.,]+$", var):
        if re.match(r"\d+$", var):  # integer
            var = int(var)
        elif re.match(r"((\d+\.(\d+)?)|(\.\d+))$", var):  # float
            var = float(var)
        elif re.match(r"((\d+,(\d+)?)|(,\d+))$", var):  # float
            var = float(var.replace(",", "."))
    elif re.match(r"(True)|(False)$", var, re.IGNORECASE):
        var = True if var[0].lower() == "t" else False
    return var


def read_toml(path_to_file: Path) -> dict:
    with open(path_to_file, "r") as fid:
        text = fid.read()
        # Docker doesn't like tomllib to read from binary data...
        info = tomli_r.loads(text)
    return info


class DMCConfig:
    """
    reads the standard streamlit config and looks for the additional segment [DMC], where configs specific for
    this app is stored in.
    Possible config keys:
    - requiredDataIdentifiers: Array of data identifiers, that must be present in a DMC, e.g. ['P', 'S|T', 'V'],
    whereas '|' signifies an OR, i.e. the data identifier S or T must be present in the code, the identifiers P
    and V required without any other option
    """

    _default = {
        "UseMessageEnvelope": True,
        "UseFormatEnvelope": True,
        "RectangularDMC": False,
        "NumberQuietZoneModules": 2,
        "ExplainDataIdentifiers": True,
        "requiredDataIdentifiers": None,
        "Title": "Data-Matrix-Code Service",
        "Header": None,
        "Subheader": None,
        "Text": None
        }

    def __init__(self, path_to_file: Union[str, Path, None] = None, prefix: str = "DMC"):
        # store input
        self.__path_to_file = path_to_file
        self.__prefix = prefix

        if path_to_file is None:
            config = dict()
        else:
            config = self._read_config(path_to_file)
            config = config[prefix] if prefix in config else dict()
        
        # check environment variables and merge dictionaries
        config_env = get_environment_variables(list(self._default.keys()), prefix)

        self.config = config_env | config
        print(f"DEBUG [DMCConfig.__init__]: config_env={config_env}, config={config} => self.config={self.config}")

    def __getitem__(self, key: str):
        return self.get_default_values(key)

    def __repr__(self):
        init = []
        if self.__path_to_file:
            init.append(f"path_to_file={self.__path_to_file}")
        init.append(f"prefix={self.__prefix}")

        call = f"DMCConfig({', '.join(init)})"
        return f"{call}: {self.config}"
    
    @staticmethod
    def _read_config(path_to_file: Union[str, Path]) -> Union[Dict[str, Any], dict]:
        path_to_file = Path(path_to_file).with_suffix(".toml")
        if not path_to_file.exists():
            UserWarning(f"Config file {path_to_file.as_posix()} does not exist.")
            return dict()
        # read file
        print(f"DEBUG: DMCConfig()._read_config(): path_to_file={path_to_file.as_posix()}")
        return read_toml(path_to_file)

    def required_dis(self, flatten: bool = False) -> Union[List[List[str]], list]:
        key = "requiredDataIdentifiers"
        dis = []
        if self.config and key in self.config:
            # check for list

            dis = self.config[key] if key in self.config else []

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

    def check_for_required_dis(self, data_identifiers: Union[List[str], Dict[str, str]]) -> Union[List[List[str]], list]:
        # process input if it is the entire
        if isinstance(data_identifiers, dict):
            data_identifiers = data_identifiers.keys()
        
        missing_dis = []
        # loop through required data identifiers
        for dis in self.required_dis():
            # check if this (required) identifier is in the messages
            if not any([di in data_identifiers for di in dis]):
                missing_dis.append(dis)
        return missing_dis
    
    def isrequireddi(self, data_identifier: str) -> list:
        for dis in self.required_dis():
            if data_identifier in dis:
                return dis
        return []
    
    def get_default_values(self, key: str):
        if key in self.config:
            return self.config[key]
        elif key in self._default:
            return self._default[key]
        else:
            raise ValueError(f"Unknown key '{key}' for configuration and default parameters.")


def create_streamlit_config(path_to_config: Union[str, Path] = ".streamlit/config.toml") -> bool:
    """
    Looks for specified environment variables that define the streamlit config.
    Creates a config file if it finds settings.
    """
    # define options to look for
    options = {
        "theme": ["base", "primaryColor"],
        "browser": ["gatherUsageStats"]
    }

    # FIXME: streamlit works natively with environment variables!
    # TODO: read file with default values first
    path_to_config = Path(path_to_config)
    settings = dict()
    if path_to_config.exists() and path_to_config.is_file():
        settings = read_toml(path_to_config)
    elif not path_to_config.parent.is_dir():
        path_to_config.parent.mkdir()
    
    # read environment variables
    for opt in options:
        # get settings from environment
        envs = get_environment_variables(options[opt], "STREAMLIT")

        # merge environment and file variables
        config = settings[opt] | envs if opt in settings else envs
        # save merged config
        if envs:
            settings[opt] = config
    
    # replace config file with new, merged config
    if settings:
        # TODO: make sure to replace the file (not just append)
        with open(path_to_config, "wb+") as fid:
            tomli_w.dump(settings, fid)
    return True


if __name__ == "__main__":
    # config1 = DMCConfig(Path(".streamlit/config.toml"))
    # print(config1)
    # config1.required_dis()

    os.environ.setdefault("DMC_NUMBER_QUIET_ZONE_MODULES", "10")
    os.environ.setdefault("DMC_REQUIRED_DATA_IDENTIFIERS", '["P", "S|T", "V"]')
    os.environ.setdefault("DMC_USE_FORMAT_ENVELOPE", "false")

    keys = ["UseMessageEnvelope", "UseFormatEnvelope", "RectangularDMC", "NumberQuietZoneModules", "ExplainDataIdentifiers"]
    # out = get_environment_variables(keys, "DMC")
    config2 = DMCConfig()
    print(config2)
    config2.required_dis()

    config3 = DMCConfig(Path(".streamlit/config.toml"))
    print(config3)
    config3.required_dis()

    os.environ.setdefault("TEST_REQUIRED_DATA_IDENTIFIERS", "[S, 12T|V,50G]")
    config4 = DMCConfig(prefix="TEST")
    print(config4)
    config4.required_dis()