import csv
import os
import re


def get_abs_path(rel_path):
    """
    Get absolute path

    Args:
        rel_path: relative path to this file

    Returns absolute path
    """
    abs_path = os.path.dirname(os.path.abspath(__file__)) + os.sep + rel_path

    if not os.path.exists(abs_path):
        raise FileNotFoundError(f'grammar data file not found: {abs_path}')
    return abs_path


def load_labels(abs_path):
    """
    loads relative path file as dictionary

    Args:
        abs_path: absolute path

    Returns dictionary of mappings
    """
    with open(abs_path, encoding='utf-8') as label_tsv:
        labels = list(csv.reader(label_tsv, delimiter="\t"))
    return labels


REORDER_PATTERN = r'(?P<second>\w+: ".*?")>> (?P<first>\w+: ".*")'


def reorder(tagged_text):
    """
    Change the order of tags if required. For example:
    >>> reorder('tokens { time { minutes: "05">> hours: "11" } }')
    # tokens { time { hours: "11" minutes: "05"} }
    """
    res = []
    for tag in tagged_text.split('tokens '):
        match = re.search(REORDER_PATTERN, tag)
        if match:
            groups = match.groupdict()

            original = f"{groups['second']}>> {groups['first']}"
            reordered = f"{groups['first']} {groups['second']}"
            new = tag.replace(original, reordered)

            res.append(new)
        else:
            res.append(tag)

    return 'tokens '.join(res)


# Punctuation that is split off into standalone tokens before tagging and
# re-attached after verbalization. Hyphens and apostrophes are word-internal
# in Ukrainian and must not be split.
_PUNCT_SPLIT = re.compile(r'\s*([,.!?;:…()«»])\s*')
_ATTACH_BEFORE = re.compile(r'\s+([,.!?;:…»)])')
_ATTACH_AFTER = re.compile(r'([«(])\s+')


def separate_punctuation(text):
    """
    Pads punctuation with spaces so each mark becomes its own token, e.g.
    >>> separate_punctuation('сто гривень, дякую!')
    'сто гривень , дякую !'
    """
    return ' '.join(_PUNCT_SPLIT.sub(r' \1 ', text).split())


def attach_punctuation(text):
    """
    Re-attaches punctuation tokens to the neighbouring words, e.g.
    >>> attach_punctuation('₴100 , дякую !')
    '₴100, дякую!'
    """
    return _ATTACH_AFTER.sub(r'\1', _ATTACH_BEFORE.sub(r'\1', text))
