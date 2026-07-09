import pynini
from pynini.lib import pynutil

from ukr.graph_utils import GraphFst
from ukr.taggers.cardinal import CardinalFst


class IpFst(GraphFst):
    """
    Finite state transducer for IPv4 addresses, e.g.
        сто дев'яносто два крапка сто шістдесят вісім крапка один крапка один
            -> word { name: "192.168.1.1" }

    Exactly four dotted groups are required, so version numbers and ordinary
    «крапка» mentions never match.

    Args:
        cardinal: CardinalFst
    """

    def __init__(self, cardinal: CardinalFst):
        super().__init__(name="ip", kind="classify")

        group = pynini.union(
            cardinal.graph_zero, cardinal.graph_digit, cardinal.graph_teen,
            cardinal.graph,
        ) @ pynini.union(*(str(value) for value in range(256)))

        dot_group = pynini.cross(" крапка ", ".") + group
        graph = group + dot_group ** 3

        graph = pynutil.insert("word { name: \"") + graph + pynutil.insert("\" }")
        self.fst = graph.optimize()
