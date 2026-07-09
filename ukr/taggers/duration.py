import pynini
from pynini.lib import pynutil

from ukr.graph_utils import NEMO_NON_BREAKING_SPACE, GraphFst
from ukr.taggers.cardinal import CardinalFst
from ukr.utils import get_abs_path


class DurationFst(GraphFst):
    """
    Finite state transducer for durations and half-quantities, e.g.
        дві години тридцять хвилин -> word { name: "2 год 30 хв" }
        сорок хвилин -> word { name: "40 хв" }
        півтори години -> word { name: "1.5 год" }
        пів кілограма / півгодини -> word { name: "0.5 кг" / "0.5 год" }

    Time-of-day uses ordinal hours («сьома година»), durations use cardinals
    («дві години»), so the two grammars do not overlap. Standalone durations
    require a multi-digit number (single digits keep the words, protecting
    idioms like «п'ять хвилин на дванадцяту»); compounds may use any digit.

    Args:
        cardinal: CardinalFst
    """

    def __init__(self, cardinal: CardinalFst):
        super().__init__(name="duration", kind="classify")

        nbsp = pynini.cross(" ", NEMO_NON_BREAKING_SPACE)

        number_any = cardinal.graph | cardinal.graph_digit
        number_multi = cardinal.graph

        hour_u = pynini.cross(pynini.union("годин", "години", "годину"), "год")
        minute_u = pynini.cross(pynini.union("хвилин", "хвилини", "хвилину"), "хв")
        second_u = pynini.cross(pynini.union("секунд", "секунди", "секунду"), "с")

        def part(number, unit):
            return number + nbsp + unit

        compound = pynini.union(
            part(number_any, hour_u) + nbsp + part(number_any, minute_u)
            + pynini.closure(nbsp + part(number_any, second_u), 0, 1),
            part(number_any, minute_u) + nbsp + part(number_any, second_u),
        )
        standalone = part(number_multi, hour_u | minute_u | second_u)

        # пів / півтора / півтори + any known unit (measure or duration)
        measure_unit = pynini.invert(pynini.string_file(get_abs_path("data/measurements.tsv")))
        any_unit = measure_unit | hour_u | minute_u | second_u
        half = pynini.cross(pynini.union("півтора", "півтори"), "1.5") + nbsp + any_unit
        half |= pynini.cross("пів", "0.5") + nbsp + any_unit
        # one-word forms: півгодини, півкілограма, ...
        half |= pynini.cross("пів", "0.5") + pynutil.insert(NEMO_NON_BREAKING_SPACE) + any_unit

        graph = compound | standalone | half
        graph = pynutil.insert("word { name: \"") + graph + pynutil.insert("\" }")
        self.fst = graph.optimize()
