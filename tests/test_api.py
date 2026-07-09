import json
import subprocess
import sys

import pytest

import ukr
from ukr.wfst import InverseNormalizer, get_normalizer, normalize


def test_package_exports():
    assert ukr.__version__ == "0.1.9"
    assert ukr.normalize is normalize
    assert ukr.InverseNormalizer is InverseNormalizer


def test_normalize_basic():
    assert normalize("двадцять дві тисячі сто один") == "22101"


def test_normalize_is_case_insensitive_but_preserves_plain_words():
    assert normalize("Київ витратив СТО ГРИВЕНЬ") == "Київ витратив ₴100"


def test_normalize_json():
    assert normalize("сьома година двадцять п'ять хвилин", json=True) == '[{"time": "07:25"}]'


@pytest.mark.parametrize("text", [
    'він сказав "привіт"',
    r"шлях C:\\temp",
    "емодзі 🙂",
    "керування\x01символом",
])
def test_normalize_json_is_valid_for_arbitrary_words(text):
    result = normalize(text, json=True)

    assert json.loads(result)


def test_normalizer_is_singleton():
    assert get_normalizer() is get_normalizer()


def test_normalize_empty_raises():
    with pytest.raises(ValueError):
        normalize("   ")


def test_normalize_type_error():
    with pytest.raises(TypeError):
        normalize(None)


def test_cli_roundtrip():
    out = subprocess.run(
        [sys.executable, "-m", "ukr"],
        input="двадцять дві тисячі сто один\n",
        capture_output=True,
        text=True,
        check=True,
    )
    assert out.stdout.strip() == "22101"
