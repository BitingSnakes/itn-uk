import pytest

from ukr.wfst import normalize


@pytest.mark.parametrize("spoken,expected", [
    ("нуль один нуль тридцять", '01030'),
    ("нуль сорок дев'ять нуль нуль", '04900'),
    ("нуль сім нуль нуль вісім", '07008'),
])
def test_code(spoken, expected):
    assert normalize(spoken) == expected


@pytest.mark.parametrize("spoken,expected", [
    # too short / too long for a postal code
    ("нуль шістдесят сім", 'нуль 67'),
    ("нуль шістдесят сім сто двадцять три сорок п'ять шістдесят сім", '0671234567'),
])
def test_code_no_false_positives(spoken, expected):
    assert normalize(spoken) == expected
