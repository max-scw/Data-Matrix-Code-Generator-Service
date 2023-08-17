import os
import re

from typing import List, Dict, Any


def camel_case_split(identifier):
    matches = re.finditer(".+?(?:(?<=[a-z])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])|$)", identifier)
    return [m.group(0) for m in matches]


def get_environment_variables(camel_case_keys: List[str], prefix: str) -> Dict[str, Any]:
    environment_config = dict()
    for ky in camel_case_keys:
        # build name of environment variable
        name = (f"{prefix}_" + "_".join(camel_case_split(ky))).upper()
        val = os.environ.get(name)
        if val is not None:
            environment_config[ky] = val
    return environment_config


if __name__ == "__main__":
    keys = ["UseMessageEnvelope", "UseFormatEnvelope", "RectangularDMC", "NumberOfQuietZoneModuls", "ExplainDataIdentifiers"]

    out = get_environment_variables(keys, "DMC")
