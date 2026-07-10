import pytest

from ukr.taggers.whitelist import WhitelistFst as Tagger
from ukr.verbalizers.whitelist import WhitelistFst as Verbalizer
from ukr.wfst import apply_fst_text, normalize


@pytest.mark.parametrize(
    "spoken,expected",
    [
        ("надішли ес ем ес", "надішли SMS"),
        ("підключи ю ес бі та вай фай", "підключи USB та Wi-Fi"),
        ("джі пі ес і ей ай", "GPS і AI"),
        ("ЕС ЕМ ЕС", "SMS"),
    ],
)
def test_whitelist(spoken, expected):
    assert normalize(spoken) == expected


def test_whitelist_tagger_and_verbalizer():
    tagged = apply_fst_text("ес ем ес", Tagger().fst)
    assert tagged == 'whitelist { name: "SMS" }'
    assert apply_fst_text(tagged, Verbalizer().fst) == "SMS"


def test_whitelist_json():
    assert normalize("ес ем ес", json=True) == '[{"whitelist": "SMS"}]'

