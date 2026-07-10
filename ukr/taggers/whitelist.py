import pynini
from pynini.lib import pynutil

from ukr.graph_utils import GraphFst, convert_space
from ukr.utils import get_abs_path


class WhitelistFst(GraphFst):
    """Classifies high-priority spoken abbreviations and fixed phrases."""

    def __init__(self):
        super().__init__(name="whitelist", kind="classify")
        replacements = pynini.string_file(get_abs_path("data/whitelist.tsv"))
        graph = pynutil.insert('name: "') + convert_space(replacements) + pynutil.insert('"')
        self.fst = self.add_tokens(graph).optimize()

