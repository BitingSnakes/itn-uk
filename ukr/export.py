"""Export the compiled ITN grammars for use outside Python.

Writes plain OpenFST binary FSTs (loadable with ``fst::StdVectorFst::Read``
in C++, no FAR extension needed) and a single FAR archive:

    ukr_itn_tagger.fst      tokenize-and-classify grammar
    ukr_itn_verbalizer.fst  verbalizer grammar
    ukr_itn.far             both grammars keyed as TAGGER / VERBALIZER

Usage::

    python -m ukr.export [output_dir]
"""

import argparse
import os

import pynini

TAGGER_FST = 'ukr_itn_tagger.fst'
VERBALIZER_FST = 'ukr_itn_verbalizer.fst'
FAR_FILE = 'ukr_itn.far'


def export_grammars(output_dir: str) -> dict:
    """Compile the grammars and write them to ``output_dir``.

    Returns a mapping of grammar name to written file path.
    """
    from ukr.wfst import get_normalizer

    os.makedirs(output_dir, exist_ok=True)
    normalizer = get_normalizer()

    tagger = normalizer.classify.fst.optimize()
    verbalizer = normalizer.verbalize_final.fst.optimize()

    paths = {
        'tagger': os.path.join(output_dir, TAGGER_FST),
        'verbalizer': os.path.join(output_dir, VERBALIZER_FST),
        'far': os.path.join(output_dir, FAR_FILE),
    }

    tagger.write(paths['tagger'])
    verbalizer.write(paths['verbalizer'])

    with pynini.Far(paths['far'], mode='w', arc_type='standard') as far:
        # FAR keys must be in lexicographic order for FarWriter.
        far['TAGGER'] = tagger
        far['VERBALIZER'] = verbalizer

    return paths


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog='python -m ukr.export',
        description='Export compiled Ukrainian ITN grammars as OpenFST binaries',
    )
    parser.add_argument('output_dir', nargs='?', default='grammars_export',
                        help='directory to write the FST/FAR files to (default: grammars_export)')
    args = parser.parse_args(argv)

    paths = export_grammars(args.output_dir)
    for name, path in paths.items():
        print(f'{name}: {path} ({os.path.getsize(path)} bytes)')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
