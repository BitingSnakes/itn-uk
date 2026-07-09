import pytest

from ukr.wfst import normalize


@pytest.mark.parametrize("spoken,expected", [
    ("дві години тридцять хвилин", '2 год 30 хв'),
    ("три хвилини двадцять секунд", '3 хв 20 с'),
    ("сорок хвилин", '40 хв'),
    ("двадцять чотири години", '24 год'),
    ("півтори години", '1.5 год'),
    ("півтора кілограма", '1.5 кг'),
    ("пів кілограма", '0.5 кг'),
    ("півгодини", '0.5 год'),
])
def test_duration(spoken, expected):
    assert normalize(spoken) == expected


@pytest.mark.parametrize("spoken,expected", [
    # time-of-day idioms must stay with the TIME grammar
    ("сьома година двадцять п'ять хвилин", '07:25'),
    ("п'ять хвилин на дванадцяту", '11:05'),
    ("сорок сім хвилин на двадцять другу", '21:47'),
    ("за чверть одинадцята", '10:45'),
])
def test_duration_does_not_shadow_time(spoken, expected):
    assert normalize(spoken) == expected
