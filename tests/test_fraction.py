import pytest

from ukr.wfst import normalize


@pytest.mark.parametrize("spoken,expected", [
    ("одна друга", '1/2'),
    ("одна третя", '1/3'),
    ("одна чверть", '1/4'),
    ("дві третіх", '2/3'),
    ("дві треті", '2/3'),
    ("три чверті", '3/4'),
    ("сім восьмих", '7/8'),
    ("п'ять шостих", '5/6'),
    ("одна двадцять п'ята", '1/25'),
    ("мінус три двадцять п'ятих", '-3/25'),
    ("три шістнадцятих", '3/16'),
    ("одна сьома", '1/7'),
])
def test_fraction(spoken, expected):
    assert normalize(spoken) == expected


@pytest.mark.parametrize("spoken,expected", [
    # powers of ten must stay decimals
    ("одна десята", '0.1'),
    ("нуль цілих одна десята", '0.1'),
    # time grammar must keep чверть phrases
    ("за чверть одинадцята", '10:45'),
    ("чверть на одинадцяту", '10:15'),
])
def test_fraction_does_not_shadow_other_classes(spoken, expected):
    assert normalize(spoken) == expected
