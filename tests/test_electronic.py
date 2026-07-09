import pytest

from ukr.wfst import normalize


@pytest.mark.parametrize("spoken,expected", [
    ("іван крапка петренко собака джімейл крапка ком", 'ivan.petrenko@gmail.com'),
    ("адмін собака укрнет", 'admin@ukr.net'),
    ("олег дев'яносто дев'ять собака гмейл крапка ком", 'oleh99@gmail.com'),
    ("інфо собака компанія крапка ком крапка юей", 'info@kompaniia.com.ua'),
    ("ве ве ве крапка приклад крапка юей", 'www.pryklad.ua'),
])
def test_electronic(spoken, expected):
    assert normalize(spoken) == expected


@pytest.mark.parametrize("spoken,expected", [
    ("собака гавкає", 'собака гавкає'),
    ("крапка з комою", 'крапка з комою'),
])
def test_electronic_no_false_positives(spoken, expected):
    assert normalize(spoken) == expected
