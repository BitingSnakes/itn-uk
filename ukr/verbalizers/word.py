import pynini
from pynini.lib import pynutil

from ukr.graph_utils import NEMO_CHAR, NEMO_SIGMA, GraphFst, delete_space


class WordFst(GraphFst):
    """
    Finite state transducer for verbalizing plain tokens
        e.g. tokens { name: "sleep" } -> sleep
    """

    def __init__(self):
        super().__init__(name="word", kind="verbalize")
        chars = pynini.closure(NEMO_CHAR - " ", 1)
        char = pynutil.delete("name:") + delete_space + pynutil.delete("\"") + chars + pynutil.delete("\"")
        graph = char @ pynini.cdrewrite(pynini.cross("\u00A0", " "), "", "", NEMO_SIGMA)

        graph = self.delete_tokens(graph)
        self.fst = graph.optimize()
