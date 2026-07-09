import pytest

from ukr.utils import attach_punctuation, separate_punctuation
from ukr.wfst import normalize


def test_separate_punctuation():
    assert separate_punctuation('сто гривень, дякую!') == 'сто гривень , дякую !'


def test_attach_punctuation():
    assert attach_punctuation('₴100 , дякую !') == '₴100, дякую!'


@pytest.mark.parametrize("spoken,expected", [
    ("сто гривень, будь ласка!", '₴100, будь ласка!'),
    ("це трапилося дві тисячі дев'ятнадцятого числа.", 'це трапилося 2019-го числа.'),
    ("скільки? двадцять два метри!", 'скільки? 22 м!'),
    ("«сьома година двадцять п'ять хвилин» — так.", '«07:25» — так.'),
    ("ціна (сто євро) підходить", 'ціна (€100) підходить'),
    ("дві третіх, або шістдесят сім відсотків", '2/3, або 67 %'),
    # apostrophes and hyphens are word-internal and must survive
    ("будь-що п'яте", "будь-що п'яте"),
])
def test_normalize_with_punctuation(spoken, expected):
    assert normalize(spoken) == expected
