import pynini
from pynini.lib import pynutil

from ukr.graph_utils import NEMO_NOT_QUOTE, GraphFst, delete_space


class FractionFst(GraphFst):
    """
    Finite state transducer for verbalizing fractions, e.g.
        fraction { numerator: "2" denominator: "3" } -> 2/3
        fraction { negative: "true" numerator: "1" denominator: "2" } -> -1/2
    """

    def __init__(self):
        super().__init__(name="fraction", kind="verbalize")

        optional_sign = pynini.closure(
            pynutil.delete("negative:")
            + delete_space
            + pynutil.delete("\"true\"")
            + delete_space
            + pynutil.insert("-"),
            0,
            1,
        )
        numerator = (
            pynutil.delete("numerator:")
            + delete_space
            + pynutil.delete("\"")
            + pynini.closure(NEMO_NOT_QUOTE, 1)
            + pynutil.delete("\"")
        )
        denominator = (
            pynutil.delete("denominator:")
            + delete_space
            + pynutil.delete("\"")
            + pynini.closure(NEMO_NOT_QUOTE, 1)
            + pynutil.delete("\"")
        )

        graph = optional_sign + numerator + delete_space + pynutil.insert("/") + denominator
        delete_tokens = self.delete_tokens(graph)
        self.fst = delete_tokens.optimize()
