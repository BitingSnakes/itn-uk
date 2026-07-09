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


@pytest.mark.parametrize("spoken,expected", [
    ("з дев'ятої до вісімнадцятої години", 'з 09:00 до 18:00'),
    ("від восьмої до сімнадцятої години", 'від 08:00 до 17:00'),
])
def test_time_range(spoken, expected):
    assert normalize(spoken) == expected


@pytest.mark.parametrize("spoken,expected", [
    ("з першого по п'яте січня", 'з 1 по 5 січня'),
    ("від десятого до двадцятого березня", 'від 10 до 20 березня'),
])
def test_date_range(spoken, expected):
    assert normalize(spoken) == expected


def test_time_range_requires_hour_word():
    # without «години» the phrase may be about anything -> untouched
    assert normalize("з першої по п'яту спробу") == "з першої по п'яту спробу"
