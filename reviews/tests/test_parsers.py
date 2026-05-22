# reviews/tests/test_parsers.py
import pytest
from reviews.parsers import parse_uploaded_file
from django.core.files.uploadedfile import SimpleUploadedFile


def make_file(name, content):
    return SimpleUploadedFile(name, content.encode("utf-8"))


def test_txt():
    f = make_file("reviews.txt", "Ótimo produto\nPéssimo atendimento\n")
    assert parse_uploaded_file(f) == ["Ótimo produto", "Péssimo atendimento"]


def test_csv_with_header():
    f = make_file(
        "reviews.csv", "text,score\nÓtimo produto,5\nPéssimo atendimento,1")
    assert parse_uploaded_file(f) == ["Ótimo produto", "Péssimo atendimento"]


def test_json_list_of_strings():
    f = make_file("reviews.json", '["Ótimo produto", "Péssimo atendimento"]')
    assert parse_uploaded_file(f) == ["Ótimo produto", "Péssimo atendimento"]


def test_json_original_format():
    f = make_file("reviews.json",
                  '{"raw_text_list": ["review 1", "review 2"]}')
    assert parse_uploaded_file(f) == ["review 1", "review 2"]


def test_unsupported_format():
    with pytest.raises(ValueError, match="Formato não suportado"):
        parse_uploaded_file(make_file("reviews.xlsx", "data"))
