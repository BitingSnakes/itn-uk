import pynini
from pynini.lib import pynutil

from ukr.graph_utils import NEMO_NON_BREAKING_SPACE, GraphFst
from ukr.taggers.cardinal import CardinalFst


class VersionFst(GraphFst):
    """
    Finite state transducer for version numbers, gated on «версія», e.g.
        версія два крапка п'ять -> word { name: "версія 2.5" }
        версії три крапка десять крапка один -> word { name: "версії 3.10.1" }
        версія п'ять -> word { name: "версія 5" }

    Args:
        cardinal: CardinalFst
    """

    def __init__(self, cardinal: CardinalFst):
        super().__init__(name="version", kind="classify")

        keyword = pynini.union("версія", "версії", "версію", "версією")
        number = pynini.union(
            cardinal.graph_zero, cardinal.graph_digit, cardinal.graph_teen,
            cardinal.graph,
        )

        graph = (
            keyword
            + pynini.cross(" ", NEMO_NON_BREAKING_SPACE)
            + number
            + pynini.closure(pynini.cross(" крапка ", ".") + number)
        )
        graph = pynutil.insert("word { name: \"") + graph + pynutil.insert("\" }")
        self.fst = graph.optimize()
