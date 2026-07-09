"""Top-level ITN pipeline: tag text with the classifier FST, reorder
non-deterministic tags, then verbalize.

Grammars are expensive to build (a few seconds), so they are constructed
lazily on first use and cached for the lifetime of the process.
"""

import threading

import pynini

from ukr.utils import reorder


def find_tags(text: str, tagger) -> 'pynini.FstLike':
    """
    Given text use tagger Fst to tag text

    Args:
        text: sentence

    Returns: tagged lattice
    """
    lattice = text @ tagger
    return lattice


def select_tag(lattice: 'pynini.FstLike') -> str:
    """
    Given tagged lattice return shortest path

    Args:
        lattice: tagged lattice

    Returns: shortest path
    """
    tagged_text = pynini.shortestpath(lattice, nshortest=1, unique=True).string()
    return tagged_text


def apply_fst_text(text: str, fst) -> str:
    """Apply ``fst`` to ``text`` and return the shortest-path output string."""
    text = pynini.escape(text)
    tagged_lattice = find_tags(text, fst)
    tagged_text = select_tag(tagged_lattice)

    return tagged_text


class InverseNormalizer:
    """Builds (or loads) the tagger and verbalizer grammars and applies them.

    Instances are safe to share between threads once constructed.
    """

    def __init__(self):
        from ukr.taggers.tokenize_and_classify import ClassifyFst
        from ukr.verbalizers.verbalize_final import VerbalizeFinalFst

        self.classify = ClassifyFst()
        self.verbalize_final = VerbalizeFinalFst()
        self._verbalize_json = self.verbalize_final.as_json()

    def normalize(self, text: str, json: bool = False) -> str:
        """
        Apply Inverse Text Normalization (ITN) to ``text``.

        :param text: input sentence (verbalized form)
        :param json: if True, return a JSON string of tagged tokens
        :return: normalized text (or JSON string)
        :raises ValueError: if the input is empty
        """
        if not isinstance(text, str):
            raise TypeError(f"expected str, got {type(text).__name__}")
        text = text.strip()
        if not text:
            raise ValueError("input text is empty")

        classified = apply_fst_text(text, self.classify.fst)
        classified = reorder(classified)

        if json:
            return apply_fst_text(classified, self._verbalize_json)
        return apply_fst_text(classified, self.verbalize_final.fst)


_normalizer = None
_normalizer_lock = threading.Lock()


def get_normalizer() -> InverseNormalizer:
    """Return the shared :class:`InverseNormalizer`, building it on first call."""
    global _normalizer
    if _normalizer is None:
        with _normalizer_lock:
            if _normalizer is None:
                _normalizer = InverseNormalizer()
    return _normalizer


def normalize(text: str, json: bool = False) -> str:
    """
    Apply Inverse Text Normalization (ITN) for the given text

    :param text: given text
    :param json: if True result would be in json
    :return: return normalized text
    """
    return get_normalizer().normalize(text, json=json)


# Backwards-compatible module attributes (``classifyFst``, ``verbalizeFinalFst``,
# ``graph``, ``json_graph``) — resolved lazily so importing this module stays cheap.
def __getattr__(name):
    if name == 'classifyFst':
        return get_normalizer().classify
    if name == 'verbalizeFinalFst':
        return get_normalizer().verbalize_final
    if name == 'graph':
        n = get_normalizer()
        return pynini.compose(n.classify.fst, n.verbalize_final.fst).optimize()
    if name == 'json_graph':
        n = get_normalizer()
        return pynini.compose(n.classify.fst, n._verbalize_json).optimize()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
