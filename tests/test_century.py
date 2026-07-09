import pytest

from ukr.wfst import normalize


@pytest.mark.parametrize("spoken,expected", [
    ("дев'ятнадцяте століття", 'XIX століття'),
    ("у двадцять першому столітті", 'у XXI столітті'),
    ("п'яте сторіччя", 'V сторіччя'),
    ("третього тисячоліття", 'III тисячоліття'),
])
def test_century(spoken, expected):
    assert normalize(spoken) == expected
