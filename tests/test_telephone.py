import pytest

from ukr.wfst import normalize


@pytest.mark.parametrize("spoken,expected", [
    # grouped dictation (most common ASR pattern)
    ("нуль шістдесят сім сто двадцять три сорок п'ять шістдесят сім", '0671234567'),
    # with ASR punctuation between groups
    ("нуль шістдесят сім, сто двадцять три, сорок п'ять, шістдесят сім", '0671234567'),
    # international prefix, digit-by-digit
    ("плюс три вісім нуль шістдесят сім один два три чотири п'ять шість сім", '+380671234567'),
    ("плюс тридцять вісім нуль п'ятдесят сто двадцять три сорок п'ять шістдесят сім", '+380501234567'),
    # fully digit-by-digit
    ("нуль один два три чотири п'ять шість сім вісім дев'ять", '0123456789'),
    # mixed groups with bare tens (сорок -> 40)
    ("нуль шістдесят сім сорок сорок сорок п'ять шість", '0674040456'),
])
def test_telephone(spoken, expected):
    assert normalize(spoken) == expected


@pytest.mark.parametrize("spoken,expected", [
    # too short to be a phone number: stays as before
    ("нуль шістдесят сім", 'нуль 67'),
    ("двадцять дві тисячі сто один", '22101'),
    ("нуль цілих одна десята", '0.1'),
])
def test_telephone_no_false_positives(spoken, expected):
    assert normalize(spoken) == expected
