import pynini
from pynini.lib import pynutil

from ukr.graph_utils import NEMO_NOT_QUOTE, GraphFst, delete_space


class TelephoneFst(GraphFst):
    """
    Finite state transducer for verbalizing telephone numbers, e.g.
        telephone { number: "0671234567" } -> 0671234567
    """

    def __init__(self):
        super().__init__(name="telephone", kind="verbalize")

        graph = (
            pynutil.delete("number:")
            + delete_space
            + pynutil.delete("\"")
            + pynini.closure(NEMO_NOT_QUOTE, 1)
            + pynutil.delete("\"")
        )
        delete_tokens = self.delete_tokens(graph)
        self.fst = delete_tokens.optimize()
