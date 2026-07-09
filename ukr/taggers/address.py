import pynini
from pynini.lib import pynutil

from ukr.graph_utils import NEMO_NON_BREAKING_SPACE, NEMO_NOT_SPACE, GraphFst
from ukr.taggers.cardinal import CardinalFst
from ukr.utils import get_abs_path


class AddressFst(GraphFst):
    """
    Finite state transducer for street addresses, e.g.
        вулиця шевченка будинок п'ять квартира три
            -> name: "вул. шевченка, буд. 5, кв. 3"
        проспект перемоги будинок сто двадцять
            -> name: "просп. перемоги, буд. 120"

    A house number is required to trigger, so a bare street mention is left
    untouched. ASR-inserted commas between the parts are consumed.

    Args:
        cardinal: CardinalFst
    """

    def __init__(self, cardinal: CardinalFst):
        super().__init__(name="address", kind="classify")

        delete_space = pynutil.delete(" ")
        # parts may be separated by an ASR comma: "вулиця шевченка , будинок п'ять"
        sep = delete_space + pynini.closure(pynutil.delete(",") + delete_space, 0, 1)
        nbsp = pynutil.insert(NEMO_NON_BREAKING_SPACE)
        comma = pynutil.insert(",") + nbsp

        def load(name):
            return pynini.invert(pynini.string_file(get_abs_path(f"data/address/{name}.tsv")))

        street_kw = load("street")
        house_kw = load("house")
        apartment_kw = load("apartment")
        building_kw = load("building")

        number = cardinal.graph | cardinal.graph_digit

        # street name: one or two plain words (no digits — those belong to the
        # house number)
        name_word = pynini.closure(pynini.difference(NEMO_NOT_SPACE, pynini.union(*",.")), 1)
        street_name = name_word + pynini.closure(pynini.cross(" ", NEMO_NON_BREAKING_SPACE) + name_word, 0, 1)

        street = street_kw + nbsp + delete_space + street_name
        house = house_kw + nbsp + delete_space + number
        building = building_kw + nbsp + delete_space + number
        apartment = apartment_kw + nbsp + delete_space + number

        graph = (
            street
            + comma + sep + house
            + pynini.closure(comma + sep + building, 0, 1)
            + pynini.closure(comma + sep + apartment, 0, 1)
        )
        graph = pynutil.insert("word { name: \"") + graph + pynutil.insert("\" }")
        # emitted as a `word` token so the existing word verbalizer handles it
        self.fst = graph.optimize()
