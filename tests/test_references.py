import pytest

from ukr.wfst import normalize


@pytest.mark.parametrize("spoken,expected", [
    ("стаття п'ята частина друга", 'ст. 5 ч. 2'),
    ("сторінка сто двадцять", 'с. 120'),
    ("параграф третій", '§ 3'),
    ("пункт два", 'п. 2'),
    ("розділ сьомий", 'розд. 7'),
])
def test_legal(spoken, expected):
    assert normalize(spoken) == expected


@pytest.mark.parametrize("spoken,expected", [
    ("рахунок два один", 'рахунок 2:1'),
    ("з рахунком три нуль", 'з рахунком 3:0'),
])
def test_score(spoken, expected):
    assert normalize(spoken) == expected


@pytest.mark.parametrize("spoken,expected", [
    ("версія два крапка п'ять", 'версія 2.5'),
    ("версії три крапка десять крапка один", 'версії 3.10.1'),
    ("версія п'ять", 'версія 5'),
])
def test_version(spoken, expected):
    assert normalize(spoken) == expected


@pytest.mark.parametrize("spoken,expected", [
    ("сто дев'яносто два крапка сто шістдесят вісім крапка один крапка один", '192.168.1.1'),
    ("десять крапка нуль крапка нуль крапка один", '10.0.0.1'),
])
def test_ip(spoken, expected):
    assert normalize(spoken) == expected


@pytest.mark.parametrize("spoken,expected", [
    ("дев'яності роки", '90-ті роки'),
    ("у вісімдесятих роках", 'у 80-х роках'),
    ("сорокові роки", '40-ві роки'),
])
def test_decade(spoken, expected):
    assert normalize(spoken) == expected
