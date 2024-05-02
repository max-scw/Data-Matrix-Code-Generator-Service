

def rstrip_non_ascii_characters(text: str) -> str:
    i = 0
    for el in text[::-1]:
        if el.isascii():
            break
        i += 1
    return text[:-i] if i > 0 else text