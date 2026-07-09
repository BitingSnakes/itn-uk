import pynini
from pynini.lib import pynutil

from ukr.graph_utils import NEMO_NON_BREAKING_SPACE, GraphFst
from ukr.taggers.cardinal import CardinalFst


class ScoreFst(GraphFst):
    """
    Finite state transducer for sports scores, gated on «рахунок», e.g.
        рахунок два один -> word { name: "рахунок 2:1" }
        з рахунком три нуль -> з word { name: "рахунком 3:0" }

    Bare digit pairs («два один») never match — the keyword is required.

    Args:
        cardinal: CardinalFst
    """

    def __init__(self, cardinal: CardinalFst):
        super().__init__(name="score", kind="classify")

        keyword = pynini.union("рахунок", "рахунку", "рахунком")
        number = cardinal.graph_zero | cardinal.graph_digit | cardinal.graph_teen | cardinal.graph

        graph = (
            keyword
            + pynini.cross(" ", NEMO_NON_BREAKING_SPACE)
            + number
            + pynini.cross(" ", ":")
            + number
        )
        graph = pynutil.insert("word { name: \"") + graph + pynutil.insert("\" }")
        self.fst = graph.optimize()
