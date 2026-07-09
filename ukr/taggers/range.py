import pynini
from pynini.lib import pynutil

from ukr.graph_utils import NEMO_CHAR, NEMO_DIGIT, NEMO_NON_BREAKING_SPACE, GraphFst
from ukr.taggers.cardinal import CardinalFst
from ukr.utils import get_abs_path


class RangeFst(GraphFst):
    """
    Finite state transducer for numeric, time and date ranges, e.g.
        від п'яти до десяти відсотків -> name: "5–10 %"
        від ста до двохсот кілометрів -> name: "100–200 км"
        дві-три години -> name: "2–3 год"
        з дев'ятої до вісімнадцятої години -> name: "з 09:00 до 18:00"
        з першого по п'яте січня -> name: "з 1 по 5 січня"

    Numeric ranges support «від/з A до/по B [unit]» and a hyphenated
    approximation «A-B [unit]». Time ranges require the «години» word and
    date ranges require a month name — the trailing anchor is what keeps
    phrases like «з першої по п'яту спробу» out of this class. Time-of-day
    grammar owns «година» phrases; the duration units («год», «хв») are only
    recognised inside a range, where the meaning is unambiguous.

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

        numeric = (prefixed | hyphenated) + optional_unit

        # --- time and date ranges (ordinal-based) ---
        strip_suffix = pynini.closure(NEMO_DIGIT) + pynutil.delete(pynini.union("-") + pynini.closure(NEMO_CHAR))

        def load_ordinal(name):
            return pynini.invert(pynini.string_file(get_abs_path(f"data/numbers/ordinal/{name}.tsv"))) @ strip_suffix

        ordinal = pynini.union(
            load_ordinal("ordinal_digit"),
            load_ordinal("ordinal_teen"),
            load_ordinal("ordinal_ties"),
            cardinal.graph_ties + delete_space + load_ordinal("ordinal_digit"),
        )

        # з дев'ятої до вісімнадцятої години -> з 09:00 до 18:00
        pad = (NEMO_DIGIT + NEMO_DIGIT) | (pynutil.insert("0") + NEMO_DIGIT)
        hour = (ordinal @ pad) + pynutil.insert(":00")
        nbsp = pynini.cross(" ", NEMO_NON_BREAKING_SPACE)
        time_range = (
            pynini.union("з", "від")
            + nbsp + hour
            + nbsp + pynini.union("до", "по")
            + nbsp + hour
            + pynutil.delete(pynini.union(" години", " годин", " годину"))
        )

        # з першого по п'яте січня -> з 1 по 5 січня
        month = pynini.string_file(get_abs_path("data/month.tsv"))
        date_range = (
            pynini.union("з", "від")
            + nbsp + ordinal
            + nbsp + pynini.union("до", "по")
            + nbsp + ordinal
            + nbsp + month
        )

        graph = numeric | time_range | date_range
        graph = pynutil.insert("word { name: \"") + graph + pynutil.insert("\" }")
        # emitted as a `word` token so the existing word verbalizer handles it
        self.fst = graph.optimize()
