import pytest

from ukr.wfst import normalize


@pytest.mark.parametrize("spoken,expected", [
    ("одна гривня", '₴1'),
    ("одна гривня одна копійка", '₴1.01'),
    ("одна гривня двадцять одна копійка", '₴1.21'),
    ("двадцять одна гривня двадцять одна копійка", '₴21.21'),
    ("сто одинадцять доларів двадцять один цент", '$111.21'),
    ("сто одинадцять доларів і двадцять один цент", '$111.21'),
    ("двадцять один цент", '$0.21'),
    ("двадцять один копійка", '₴0.21'),
    ("сім копійок", '₴0.07'),
    ("п'ять цілих одна десята гривні", '₴5.1'),
    ("п'ять цілих одна десята мільйонів гривень", '₴5.1 мільйонів'),
    ("тридцять тисяч сто одна гривень", '₴30101'),
])
def test_money(spoken, expected):
    assert normalize(spoken) == expected


@pytest.mark.parametrize("apostrophe", ["'", "’", "ʼ"])
def test_money_accepts_ukrainian_apostrophe_variants(apostrophe):
    assert normalize(f"п{apostrophe}ять гривень") == "₴5"


@pytest.mark.parametrize("spoken,expected", [
    ("мінус п'ять гривень", "-₴5"),
    ("мінус два євро п'ятдесят євроцентів", "-€2.50"),
    ("мінус нуль цілих п'ять десятих біткоїна", "-₿0.5"),
])
def test_negative_money(spoken, expected):
    assert normalize(spoken) == expected


@pytest.mark.parametrize("spoken,expected", [
    ("сто євро", '€100'),
    ("два євро п'ятдесят євроцентів", '€2.50'),
    ("п'ятдесят євроцентів", '€0.50'),
    ("п'ять фунтів стерлінгів", '£5'),
    ("десять фунтів", '£10'),
    ("два фунти двадцять пенсів", '£2.20'),
    ("двадцять пенсів", '£0.20'),
])
def test_euro_pound(spoken, expected):
    assert normalize(spoken) == expected


@pytest.mark.parametrize("spoken,expected", [
    ("сто рублів", '₽100'),
    ("тисяча рублів", '₽1000'),
    ("п'ятдесят злотих", 'zł50'),
    ("два злотих", 'zł2'),
    ("сто єн", '¥100'),
    ("п'ять цілих п'ять десятих єни", '¥5.5'),
])
def test_major_only_currencies(spoken, expected):
    assert normalize(spoken) == expected


@pytest.mark.parametrize("spoken,expected", [
    ("сто швейцарських франків", 'CHF100'),
    ("один канадський долар", 'C$1'),
    ("п'ятдесят канадських доларів", 'C$50'),
    ("сто австралійських доларів", 'A$100'),
    ("тисяча шведських крон", 'SEK1000'),
    ("п'ятсот чеських крон", 'CZK500'),
    ("сто норвезьких крон", 'NOK100'),
    ("двісті данських крон", 'DKK200'),
    ("п'ятдесят юанів", '¥50'),
    ("тисяча рупій", '₹1000'),
    ("двісті шекелів", '₪200'),
    ("п'ять тисяч тенге", '₸5000'),
    ("триста батів", '฿300'),
    ("сто лір", '₺100'),
    ("п'ятдесят реалів", 'R$50'),
    ("тисяча вон", '₩1000'),
    ("сто дирхамів", 'AED100'),
    ("два біткоїни", '₿2'),
    ("нуль цілих п'ять десятих біткоїна", '₿0.5'),
    ("сто ларі", '₾100'),
])
def test_world_currencies(spoken, expected):
    assert normalize(spoken) == expected


@pytest.mark.parametrize("spoken,expected", [
    # «вона»/«вони» are pronouns, never the KRW currency
    ("вона сказала", 'вона сказала'),
    ("вони прийшли", 'вони прийшли'),
])
def test_currency_no_pronoun_false_positives(spoken, expected):
    assert normalize(spoken) == expected
