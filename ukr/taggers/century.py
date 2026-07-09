import pynini
from pynini.lib import pynutil

from ukr.graph_utils import NEMO_CHAR, NEMO_DIGIT, NEMO_NON_BREAKING_SPACE, GraphFst
from ukr.taggers.cardinal import CardinalFst
from ukr.utils import get_abs_path


def _to_roman(n: int) -> str:
    numerals = [(10, 'X'), (9, 'IX'), (5, 'V'), (4, 'IV'), (1, 'I')]
    out = []
    while n > 0:
        for value, sym in numerals:
            if n >= value:
                out.append(sym)
                n -= value
                break
    return ''.join(out)


class CenturyFst(GraphFst):
    """
    Finite state transducer for centuries and millennia, written with Roman
    numerals per Ukrainian typographic convention, e.g.
        дев'ятнадцяте століття -> name: "XIX століття"
        у двадцять першому столітті -> у name: "XXI столітті"
        третього тисячоліття -> name: "III тисячоліття"

    Emits a plain `name` token (with non-breaking space), so it is verbalized
    by the existing word grammar.

    Args:
        cardinal: CardinalFst
    """

    def __init__(self, cardinal: CardinalFst):
        super().__init__(name="century", kind="classify")

        delete_space = pynutil.delete(" ")
        strip_suffix = pynini.closure(NEMO_DIGIT) + pynutil.delete(pynini.union("-") + pynini.closure(NEMO_CHAR))

        def load(name):
            return pynini.invert(pynini.string_file(get_abs_path(f"data/numbers/ordinal/{name}.tsv"))) @ strip_suffix

        ordinal_digit = load("ordinal_digit")
        ordinal_teen = load("ordinal_teen")
        ordinal_ties = load("ordinal_ties")

        number = pynini.union(
            ordinal_digit,
            ordinal_teen,
            ordinal_ties,
            cardinal.graph_ties + delete_space + ordinal_digit,
        )

        roman = pynini.union(*(pynini.cross(str(n), _to_roman(n)) for n in range(1, 22)))
        number = (number @ roman).optimize()

        century_word = pynini.union(
            "століття", "столітті", "століть", "сторіччя", "сторіччі",
            "тисячоліття", "тисячолітті", "тисячоліть",
        )

        graph = number + pynini.cross(" ", NEMO_NON_BREAKING_SPACE) + century_word
        graph = pynutil.insert("word { name: \"") + graph + pynutil.insert("\" }")
        # emitted as a `word` token so the existing word verbalizer handles it
        self.fst = graph.optimize()
