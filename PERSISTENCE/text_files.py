import csv
from pathlib import Path


def read_text(path):
    raw = Path(path).read_bytes()
    for encoding in ("utf-8-sig", "cp1252", "latin-1"):
        try:
            return (
                raw.decode(encoding)
                .replace("\r\n", "\n")
                .replace("\r", "\n")
            )
        except UnicodeDecodeError:
            continue
    raise UnicodeError("Could not read the file.")


def write_text(path, text):
    Path(path).write_text(text, encoding="utf-8")

def read_tsv(path):
    with Path(path).open(encoding="utf-8", newline="") as file:
        return list(csv.reader(file, delimiter="\t", quoting=csv.QUOTE_NONE))


def write_tsv(path, rows):
    with Path(path).open("w", encoding="utf-8", newline="") as file:
        csv.writer(file, delimiter="\t").writerows(rows)