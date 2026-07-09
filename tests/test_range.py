import pytest

from ukr.wfst import normalize


@pytest.mark.parametrize("spoken,expected", [
    ("від п'яти до десяти відсотків", '5–10 %'),
    ("від ста до двохсот кілометрів", '100–200 км'),
    ("від двох до трьох", '2–3'),
    ("дві-три години", '2–3 год'),
    ("п'ять-шість кілометрів", '5–6 км'),
    ("сорок-п'ятдесят хвилин", '40–50 хв'),
])
def test_range(spoken, expected):
    assert normalize(spoken) == expected


def test_range_does_not_shadow_time():
    assert normalize("сьома година двадцять п'ять хвилин") == '07:25'
