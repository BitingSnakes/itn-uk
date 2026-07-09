import pynini
from pynini.lib import pynutil

from ukr.graph_utils import NEMO_NON_BREAKING_SPACE, GraphFst
from ukr.taggers.cardinal import CardinalFst


class NumberSignFst(GraphFst):
    """
    Finite state transducer for «номер» + number, e.g.
        номер п'ять -> name: "№ 5"
        під номером двадцять два -> під name: "№ 22"

    The «номер» keyword disambiguates, so single-digit numbers are allowed
    here even though bare cardinals keep them as words.

    Args:
        cardinal: CardinalFst
    """

    def __init__(self, cardinal: CardinalFst):
        super().__init__(name="number_sign", kind="classify")

        delete_space = pynutil.delete(" ")

        keyword = pynini.union("номер", "номером", "номері", "номера", "номеру")
        number = cardinal.graph | cardinal.graph_digit

        graph = (
            pynini.cross(keyword, "№")
            + pynutil.insert(NEMO_NON_BREAKING_SPACE)
            + delete_space
            + number
        )
        graph = pynutil.insert("word { name: \"") + graph + pynutil.insert("\" }")
        # emitted as a `word` token so the existing word verbalizer handles it
        self.fst = graph.optimize()
