# reviews/parsers.py
import csv
import json
import io
from typing import List


def parse_uploaded_file(file) -> List[str]:
    filename = file.name.lower()
    content = file.read()

    if filename.endswith(".txt"):
        return _parse_txt(content)
    elif filename.endswith(".csv"):
        return _parse_csv(content)
    elif filename.endswith(".json"):
        return _parse_json(content)
    else:
        raise ValueError(f"Formato não suportado: {filename}")


def _parse_txt(content: bytes) -> List[str]:
    """Uma review por linha."""
    lines = content.decode("utf-8").splitlines()
    return [line.strip() for line in lines if line.strip()]


def _parse_csv(content: bytes) -> List[str]:
    """
    Aceita CSV com ou sem header.
    Se houver coluna chamada 'text', 'review' ou 'feedback', usa ela.
    Caso contrário, usa a primeira coluna.
    """
    text = content.decode("utf-8")
    reader = csv.DictReader(io.StringIO(text))

    KNOWN_COLUMNS = {"text", "review", "feedback", "comment", "review_text"}

    rows = list(reader)
    if not rows:
        return []

    # Detecta coluna automaticamente
    headers = [h.lower().strip() for h in rows[0].keys()]
    target_col = next((h for h in headers if h in KNOWN_COLUMNS), headers[0])

    return [
        row[target_col].strip()
        for row in rows
        if row.get(target_col, "").strip()
    ]


def _parse_json(content: bytes) -> List[str]:
    """
    Aceita três formatos:
      1. ["review 1", "review 2"]                         → lista de strings
      2. [{"text": "review 1"}, {"text": "review 2"}]     → lista de objetos
      3. {"raw_text_list": ["review 1", "review 2"]}      → formato original da API  # noqa: E501
    """
    data = json.loads(content.decode("utf-8"))

    if isinstance(data, list):
        if all(isinstance(item, str) for item in data):
            return data
        if all(isinstance(item, dict) for item in data):
            KNOWN_KEYS = {"text", "review",
                          "feedback", "comment", "review_text"}
            key = next((k for k in data[0] if k.lower() in KNOWN_KEYS), None)
            if not key:
                raise ValueError(
                    f"Nenhuma chave reconhecida no JSON. Chaves encontradas: {list(data[0].keys())}")  # noqa: E501
            return [item[key] for item in data if item.get(key, "").strip()]

    if isinstance(data, dict) and "raw_text_list" in data:
        return data["raw_text_list"]

    raise ValueError("Formato JSON não reconhecido.")
