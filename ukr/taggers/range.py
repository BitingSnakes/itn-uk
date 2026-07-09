import pynini
from pynini.lib import pynutil

from ukr.graph_utils import NEMO_NON_BREAKING_SPACE, GraphFst
from ukr.taggers.cardinal import CardinalFst
from ukr.utils import get_abs_path


class RangeFst(GraphFst):
    """
    Finite state transducer for numeric ranges, e.g.
        від п'яти до десяти відсотків -> name: "5–10 %"
        від ста до двохсот кілометрів -> name: "100–200 км"
        дві-три години -> name: "2–3 год"

    Two shapes are supported: «від/з A до/по B [unit]» and a hyphenated
    approximation «A-B [unit]». Time-of-day grammar owns «година» phrases;
    the duration units («год», «хв») are only recognised inside a range,
    where the meaning is unambiguous.

    Args:
        cardinal: CardinalFst
    """

    def __init__(self, cardinal: CardinalFst):
        super().__init__(name="range", kind="classify")

        delete_space = pynutil.delete(" ")

        number = cardinal.graph | cardinal.graph_digit

        unit = pynini.invert(pynini.string_file(get_abs_path("data/measurements.tsv")))
        duration = pynini.union(
            pynini.cross(pynini.union("година", "години", "годин", "годину"), "год"),
            pynini.cross(pynini.union("хвилина", "хвилини", "хвилин", "хвилину"), "хв"),
        )
        unit |= duration
        optional_unit = pynini.closure(
            pynini.cross(" ", NEMO_NON_BREAKING_SPACE) + unit, 0, 1
        )

        dash = pynutil.insert("–")

        # від/з A до/по B
        prefixed = (
            pynutil.delete(pynini.union("від", "з"))
            + delete_space
            + number
            + delete_space
            + pynutil.delete(pynini.union("до", "по"))
            + dash
            + delete_space
            + number
        )
        # hyphenated approximation: дві-три
        hyphenated = number + pynini.cross("-", "–") + number

        graph = (prefixed | hyphenated) + optional_unit
        graph = pynutil.insert("word { name: \"") + graph + pynutil.insert("\" }")
        # emitted as a `word` token so the existing word verbalizer handles it
        self.fst = graph.optimize()
