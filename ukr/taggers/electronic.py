import pynini
from pynini.lib import pynutil

from ukr.graph_utils import GraphFst
from ukr.taggers.cardinal import CardinalFst
from ukr.utils import get_abs_path

# Ukrainian-to-Latin romanization (KMU 2010, non-initial variants).
# Used to spell out free-form parts of e-mail addresses and URLs.
TRANSLIT = [
    ('а', 'a'), ('б', 'b'), ('в', 'v'), ('г', 'h'), ('ґ', 'g'), ('д', 'd'),
    ('е', 'e'), ('є', 'ie'), ('ж', 'zh'), ('з', 'z'), ('и', 'y'), ('і', 'i'),
    ('ї', 'i'), ('й', 'i'), ('к', 'k'), ('л', 'l'), ('м', 'm'), ('н', 'n'),
    ('о', 'o'), ('п', 'p'), ('р', 'r'), ('с', 's'), ('т', 't'), ('у', 'u'),
    ('ф', 'f'), ('х', 'kh'), ('ц', 'ts'), ('ч', 'ch'), ('ш', 'sh'),
    ('щ', 'shch'), ('ю', 'iu'), ('я', 'ia'), ('ь', ''), ("'", ''),
]


class ElectronicFst(GraphFst):
    """
    Finite state transducer for classifying e-mail addresses and web
    addresses as dictated to ASR, e.g.
        іван крапка петренко собака джімейл крапка ком
            -> electronic { address: "ivan.petrenko@gmail.com" }
        ве ве ве крапка приклад крапка юей
            -> electronic { address: "www.pryklad.ua" }

    Free-form words are romanized with the KMU-2010 transliteration; known
    providers («джімейл» -> gmail) and TLDs («ком» -> com, «юей» -> ua) come
    from data files. An e-mail requires «собака», a URL requires the
    «ве ве ве» prefix, so ordinary text never matches.

    Args:
        cardinal: CardinalFst
    """

    def __init__(self, cardinal: CardinalFst):
        super().__init__(name="electronic", kind="classify")

        delete_space = pynutil.delete(" ")

        translit = pynini.closure(pynini.union(*(pynini.cross(c, l) for c, l in TRANSLIT)), 1)
        provider = pynini.invert(pynini.string_file(get_abs_path("data/electronic/providers.tsv")))
        symbol = pynini.invert(pynini.string_file(get_abs_path("data/electronic/symbols.tsv")))
        tld = pynini.invert(pynini.string_file(get_abs_path("data/electronic/tlds.tsv")))

        number = pynini.union(
            cardinal.graph_zero,
            cardinal.graph_digit,
            cardinal.graph_teen,
            cardinal.graph_ties + pynutil.insert("0"),
            cardinal.graph_ties + delete_space + cardinal.graph_digit,
        )

        # transliteration is the fallback: known symbols, providers and TLDs
        # must win over romanizing the same spoken word letter-by-letter
        translit = pynutil.add_weight(translit, 1.0)

        word = provider | translit | number
        part = word + pynini.closure(delete_space + (symbol | word), 0)

        dot = delete_space + pynini.cross("крапка", ".") + delete_space
        # a domain is either a known provider on its own (укрнет -> ukr.net)
        # or dotted labels ending in at least one dot
        domain = provider | ((provider | translit) + pynini.closure(dot + (tld | translit), 1))

        email = part + delete_space + pynini.cross("собака", "@") + delete_space + domain

        www = pynini.cross(pynini.union("ве ве ве", "дабл ю дабл ю дабл ю"), "www")
        url = www + dot + domain

        graph = pynutil.insert("address: \"") + (email | url) + pynutil.insert("\"")
        final_graph = self.add_tokens(graph)
        self.fst = final_graph.optimize()
