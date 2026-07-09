import pynini
from pynini.lib import pynutil

from ukr.graph_utils import NEMO_DIGIT, GraphFst
from ukr.taggers.cardinal import CardinalFst


class CodeFst(GraphFst):
    """
    Finite state transducer for zero-leading digit codes such as Ukrainian
    postal codes, e.g.
        нуль один нуль тридцять -> name: "01030"

    A leading «нуль» is a strong signal that a digit string is being
    dictated (ordinary numbers never start with zero), and the length is
    pinned to the Ukrainian postal-code format (exactly five digits), so it
    cannot collide with telephone numbers or partial digit groups.

    Args:
        cardinal: CardinalFst
    """

    def __init__(self, cardinal: CardinalFst):
        super().__init__(name="code", kind="classify")

        delete_space = pynutil.delete(" ")

        group = pynini.union(
            cardinal.graph_zero,
            cardinal.graph_digit,
            cardinal.graph_teen,
            cardinal.graph_ties + pynutil.insert("0"),
            cardinal.graph_ties + delete_space + cardinal.graph_digit,
        )

        number = pynini.cross("нуль", "0") + pynini.closure(delete_space + group, 1)
        shape = pynini.accep("0") + (NEMO_DIGIT ** 4)
        number = (number @ shape).optimize()

        graph = pynutil.insert("word { name: \"") + number + pynutil.insert("\" }")
        # emitted as a `word` token so the existing word verbalizer handles it
        self.fst = graph.optimize()
