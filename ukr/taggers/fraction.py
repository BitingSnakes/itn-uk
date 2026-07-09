import pynini
from pynini.lib import pynutil

from ukr.graph_utils import GraphFst
from ukr.taggers.cardinal import CardinalFst
from ukr.utils import get_abs_path


class FractionFst(GraphFst):
    """
    Finite state transducer for classifying common fractions,
        e.g. одна друга -> fraction { numerator: "1" denominator: "2" }
             дві третіх -> fraction { numerator: "2" denominator: "3" }
             мінус три двадцять п'ятих -> fraction { negative: "true" numerator: "3" denominator: "25" }

    Powers of ten (десята, сота, тисячна) are handled by the DECIMAL grammar
    and deliberately excluded here.

    Args:
        cardinal: CardinalFst
    """

    def __init__(self, cardinal: CardinalFst):
        super().__init__(name="fraction", kind="classify")

        delete_space = pynutil.delete(" ")

        def load(name):
            return pynini.invert(pynini.string_file(get_abs_path(f"data/numbers/fraction/{name}.tsv")))

        digit_sg = load("denominator_digit_sg")
        teen_sg = load("denominator_teen_sg")
        ties_sg = load("denominator_ties_sg")
        digit_pl = load("denominator_digit_pl")
        teen_pl = load("denominator_teen_pl")
        ties_pl = load("denominator_ties_pl")

        # compound denominators: двадцять п'ята / двадцять п'ятих -> 25
        compound_sg = cardinal.graph_ties + delete_space + digit_sg
        compound_pl = cardinal.graph_ties + delete_space + digit_pl

        denominator_sg = pynini.union(digit_sg, teen_sg, ties_sg, compound_sg)
        denominator_pl = pynini.union(digit_pl, teen_pl, ties_pl, compound_pl)

        # numerator "одна" takes a feminine-singular denominator,
        # anything else takes the plural form
        numerator_one = pynini.cross(pynini.union("одна", "одну"), "1")
        numerator_many = cardinal.graph

        fraction = pynini.union(
            numerator_one + delete_space + pynutil.insert("\" denominator: \"") + denominator_sg,
            numerator_many + delete_space + pynutil.insert("\" denominator: \"") + denominator_pl,
        )
        graph = pynutil.insert("numerator: \"") + fraction + pynutil.insert("\"")

        optional_minus = pynini.closure(pynutil.insert("negative: \"true\" ") + pynutil.delete("мінус "), 0, 1)

        final_graph = optional_minus + graph
        final_graph = self.add_tokens(final_graph)
        self.fst = final_graph.optimize()
