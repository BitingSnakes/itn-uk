import pytest

from ukr.wfst import normalize


@pytest.mark.parametrize("spoken,expected", [
    ("першого січня дві тисячі першого року", '1 січня 2001 року'),
    ("третє червня дві тисячі двадцять третього", '3 червня 2023'),
    ("першого січня", '1 січня'),
    ("двадцять перше лютого", '21 лютого'),
    ("січень дві тисячі першого року", 'січень 2001 року'),
    ("січень дві тисячі першого", 'січень 2001'),
    ("дві тисячі першого рік", '2001 рік'),
    ("дев'ятсот сорок п'ятий рік до нашої ери", '945 рік до н. е.'),
    ("сто вісімдесят восьмий рік нашої ери", '188 рік н. е.'),

])
def test_month(spoken, expected):
    assert normalize(spoken) == expected


@pytest.mark.parametrize("spoken,expected", [
    ("п'ятого липня", '5 липня'),
    ("п'ятого липня дві тисячі двадцятого року", '5 липня 2020 року'),
    ("липень дві тисячі першого року", 'липень 2001 року'),
])
def test_july(spoken, expected):
    assert normalize(spoken) == expected


def test_day_above_31_is_not_normalized_as_a_date():
    assert normalize("тридцять друге січня") != "32 січня"
