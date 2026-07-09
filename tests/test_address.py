import pytest

from ukr.wfst import normalize


@pytest.mark.parametrize("spoken,expected", [
    ("вулиця шевченка будинок п'ять квартира три", 'вул. шевченка, буд. 5, кв. 3'),
    ("вулиця івана франка, будинок сім, квартира дев'ять", 'вул. івана франка, буд. 7, кв. 9'),
    ("проспект перемоги будинок сто двадцять", 'просп. перемоги, буд. 120'),
    ("вулиця миру будинок два корпус три квартира сорок", 'вул. миру, буд. 2, корп. 3, кв. 40'),
])
def test_address(spoken, expected):
    assert normalize(spoken) == expected


def test_bare_street_untouched():
    # no house number -> no abbreviation
    assert normalize("на вулиці хрещатик") == 'на вулиці хрещатик'
