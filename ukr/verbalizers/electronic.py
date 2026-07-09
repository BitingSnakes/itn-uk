import pynini
from pynini.lib import pynutil

from ukr.graph_utils import NEMO_NOT_QUOTE, GraphFst, delete_space


class ElectronicFst(GraphFst):
    """
    Finite state transducer for verbalizing electronic addresses, e.g.
        electronic { address: "ivan@gmail.com" } -> ivan@gmail.com
    """

    def __init__(self):
        super().__init__(name="electronic", kind="verbalize")

        graph = (
            pynutil.delete("address:")
            + delete_space
            + pynutil.delete("\"")
            + pynini.closure(NEMO_NOT_QUOTE, 1)
            + pynutil.delete("\"")
        )
        delete_tokens = self.delete_tokens(graph)
        self.fst = delete_tokens.optimize()
