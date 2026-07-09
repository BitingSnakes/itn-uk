import pynini
from pynini.lib import pynutil

from ukr.graph_utils import NEMO_DIGIT, GraphFst
from ukr.taggers.cardinal import CardinalFst


class TelephoneFst(GraphFst):
    """
    Finite state transducer for classifying Ukrainian telephone numbers as
    dictated to ASR. Accepts the country prefix («плюс три вісім нуль»,
    «плюс тридцять вісім нуль» -> +380) or the trunk «нуль» -> 0, followed by
    nine more digits spoken as any mix of single digits, teens, tens,
    tens-plus-digit and hundreds groups, e.g.

        нуль шістдесят сім сто двадцять три сорок п'ять шістдесят сім
            -> telephone { number: "0671234567" }
        плюс три вісім нуль шістдесят сім один два три чотири п'ять шість сім
            -> telephone { number: "+380671234567" }

    ASR punctuation between groups (commas) is consumed. The total length is
    constrained to the Ukrainian format (prefix + exactly nine digits), which
    keeps ordinary numbers out of this class.

    Args:
        cardinal: CardinalFst
    """

    def __init__(self, cardinal: CardinalFst):
        super().__init__(name="telephone", kind="classify")

        delete_space = pynutil.delete(" ")
        # ASR may punctuate between dictated groups: "нуль шістдесят сім , сто ..."
        group_sep = delete_space + pynini.closure(pynutil.delete(",") + delete_space, 0, 1)

        zero = cardinal.graph_zero
        digit = cardinal.graph_digit
        teen = cardinal.graph_teen
        ties = cardinal.graph_ties
        hundred3 = cardinal.graph_hundred_component @ (NEMO_DIGIT ** 3)

        group = pynini.union(
            zero,
            digit,
            teen,
            ties + pynutil.insert("0"),                # сорок -> 40
            ties + delete_space + digit,               # сорок п'ять -> 45
            hundred3,                                  # сто двадцять три -> 123
        )

        prefix = pynini.union(
            pynini.cross("плюс три вісім нуль", "+380"),
            pynini.cross("плюс тридцять вісім нуль", "+380"),
            pynini.cross("нуль", "0"),
        )

        number = prefix + pynini.closure(group_sep + group, 1)
        # Ukrainian numbers: prefix followed by exactly nine digits.
        shape = (pynini.accep("+380") | pynini.accep("0")) + NEMO_DIGIT ** 9
        number = (number @ shape).optimize()

        graph = pynutil.insert("number: \"") + number + pynutil.insert("\"")
        final_graph = self.add_tokens(graph)
        self.fst = final_graph.optimize()
