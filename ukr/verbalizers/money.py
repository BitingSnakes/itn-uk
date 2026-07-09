import pynini
from pynini.lib import pynutil

from ukr.graph_utils import GraphFst, delete_space
from ukr.utils import get_abs_path, load_labels
from ukr.verbalizers.decimal import DecimalFst


class MoneyFst(GraphFst):
    """
    Finite state transducer for verbalizing money, e.g.
        money { integer_part: "12" fractional_part: "05" currency: "$" } -> $12.05

    Args:
        decimal: DecimalFst
    """

    def __init__(self, decimal: DecimalFst):
        super().__init__(name="money", kind="verbalize")

        # accept every currency symbol the tagger can emit
        symbols = sorted({row[0] for row in load_labels(get_abs_path("data/currency/currency_major.tsv"))})
        units = pynini.union(*symbols)

        unit = (
                pynutil.delete("currency:")
                + delete_space
                + pynutil.delete("\"")
                + pynini.closure(units, 1)
                + pynutil.delete("\"")
        )
        optional_sign = pynini.closure(
            pynini.cross('negative: "true"', "-") + delete_space, 0, 1
        )
        graph = optional_sign + unit + delete_space + decimal.numbers
        delete_tokens = self.delete_tokens(graph)
        self.fst = delete_tokens.optimize()
