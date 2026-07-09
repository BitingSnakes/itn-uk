import pytest

from ukr.wfst import normalize


@pytest.mark.parametrize("spoken,expected", [
    ("номер п'ять", '№ 5'),
    ("під номером двадцять два", 'під № 22'),
    ("номер сто один", '№ 101'),
])
def test_number_sign(spoken, expected):
    assert normalize(spoken) == expected
