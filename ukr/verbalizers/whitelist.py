import pynini
from pynini.lib import pynutil

from ukr.graph_utils import NEMO_CHAR, GraphFst, delete_space


class WhitelistFst(GraphFst):
    """Verbalizes a whitelisted written form."""

    def __init__(self):
        super().__init__(name="whitelist", kind="verbalize")
        value = (
            pynutil.delete("name:")
            + delete_space
            + pynutil.delete('"')
            + pynini.closure(NEMO_CHAR - '"', 1)
            + pynutil.delete('"')
        )
        self.fst = self.delete_tokens(value).optimize()

    def as_json(self):
        return pynutil.insert('{"whitelist": "') + self.fst + pynutil.insert('"}')

