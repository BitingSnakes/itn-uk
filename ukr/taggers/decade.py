import pynini
from pynini.lib import pynutil

from ukr.graph_utils import NEMO_NON_BREAKING_SPACE, GraphFst

# decade forms, case-aligned with the appropriate «роки» form
DECADES = [
    ('20', 'двадцят'), ('30', 'тридцят'), ('50', "п'ятдесят"),
    ('60', 'шістдесят'), ('70', 'сімдесят'), ('80', 'вісімдесят'),
]
SUFFIXES = [('і', '-ті'), ('их', '-х'), ('им', '-м'), ('ими', '-ми')]
# stems with non-standard endings
IRREGULAR = [
    ('40-ві', 'сорокові'), ('40-х', 'сорокових'), ('40-м', 'сороковим'), ('40-ми', 'сороковими'),
    ('90-ті', "дев'яності"), ('90-х', "дев'яностих"), ('90-м', "дев'яностим"), ('90-ми', "дев'яностими"),
]


class DecadeFst(GraphFst):
    """
    Finite state transducer for decades, e.g.
        дев'яності роки -> word { name: "90-ті роки" }
        у вісімдесятих роках -> у word { name: "80-х роках" }

    The «роки» word is required, so fraction denominators («дві дев'яності»)
    and other uses are unaffected.
    """

    def __init__(self):
        super().__init__(name="decade", kind="classify")

        pairs = list(IRREGULAR)
        for digits, stem in DECADES:
            for spoken_suf, written_suf in SUFFIXES:
                pairs.append((digits + written_suf, stem + spoken_suf))

        decade = pynini.union(*(pynini.cross(s, w) for w, s in pairs))
        roky = pynini.union("роки", "років", "рокам", "роками", "роках")

        graph = decade + pynini.cross(" ", NEMO_NON_BREAKING_SPACE) + roky
        graph = pynutil.insert("word { name: \"") + graph + pynutil.insert("\" }")
        self.fst = graph.optimize()
