import re


def build_format_pattern(format_string: str, match_entire_string: bool = True) -> str:
    # break string into segments
    string_segments = re.findall(r'(?:[^\+\"\']|\"[^\"]*\"|\'[^\']*\')+', format_string)

    pattern = ""
    for seg in string_segments:
        # extract minimal number of characters
        num_min = 0
        m = re.search(r"\d+", seg)
        if m:
            num_min = int(m.group())

        # extract maximum number of characters
        num_max = num_min if num_min > 0 else 9999
        m = re.search(r"(?<=\d\.\.\.)\d+", seg)
        if m:
            num_max = int(m.group())

        # an: str.isalnum() "[^0-9a-zA-Z]+"
        # a: str.isalpha()  "[a-zA-Z]+"
        # n: str.isnumeric() "\d+(\.\d+)?"
        # else: str.isascii()
        # cases: a, n, an, explicit character sequence: ""
        m = re.match(r'".*"', seg)
        if m:
            character_pattern = re.escape(m.group()[1:-1])
            num_min, num_max = 1, 1
        elif re.match(r"an\d?", seg):  # an: str.isalnum() "[^0-9a-zA-Z]+"
            character_pattern = r"[a-zA-Z0-9\.\-\+_]"
        elif re.match(r"a\d?", seg):  # a: str.isalpha()  "[a-zA-Z]+"
            character_pattern = "[a-zA-Z]"
        elif re.match(r"n\d?", seg):  # n: str.isnumeric() "\d+(\.\d+)?"
            character_pattern = r"[0-9\.]"
        else:
            raise ValueError(f"Unknown character specification {seg} in {format_string}. "
                             f"Was expecting an/a/n or an explicit character (sequence) given in quotation marks.")

        # build pattern by add number of expected repetition
        pattern += character_pattern
        if num_min == num_max:
            if num_min > 1:
                pattern += f"{{{num_min}}}"
        else:
            pattern += f"{{{num_min},{num_max}}}"

    if match_entire_string:
        # enclose pattern to match from start to end
        pattern = "^" + pattern + "$"
    return pattern


def validate_format(format_specification: str, string_to_validate: str, strict: bool = True) -> bool:
    val_pattern = build_format_pattern(format_specification)

    m = re.match(val_pattern, string_to_validate)
    if m is None:
        if strict:
            raise ValueError(f"Validation failed! "
                             f"The string '{string_to_validate}' does not match the pattern {val_pattern} "
                             f"for format {format_specification}.")
        else:
            return False
    return True


if __name__ == "__main__":
    examples = {
        'an3+n8': ['27D20170615', '26D20170721', '25D20170202'],
        'an3+n16': ['28D2017012320170214'],
        'an3+an3...35+"+"+a1...3': ['26HLHHIBC987XY65+LK'],
        'an2+n9': ['8J211123456'],
        'an3+an2...12': ['18L37.1.3', '18L47.B.1', '18L67'],
        'an3+a2+an3...27': ['35LIECK0107EC'],
        'an3+an3...35': ['50PABC+6'],
        'an3+an1...20': ['27Q1000', '27Q1000.5'],
        'an3+an1...10': ['28Q100', '28Q100.50', '8R02.1.0', '8R03.1.5', '8R05.1.0'],
        'an3+n1...6': ['29Q10', '29Q8.5'],
        'an3+an1...5': ['30Q19', '30Q8.5'],
        'an3+an3': ['31QUSD', '31QEUR', '31Q978'],
        'an3+an1...3': ['7RMUC', '7RPCD', '7RWSH'],
        'an2+an2': ['9R01', '9R02', '9R03'],
        'an3+a2+an3...18': ['23VIE6388047V'],
        }

    for spec, tests in examples.items():
        for el in tests:
            validate_format(spec, el)
