# WFST for Ukrainian ITN

WFST-based Inverse Text Normalization (ITN) for Ukrainian, built on NVIDIA NeMo grammars and Pynini.

Supported semiotic classes: cardinal, ordinal, decimal, fraction, measure, money, date, time,
telephone, electronic (e-mail/URL), century (Roman numerals), number sign (№), ranges
(numeric/time/date), durations & half-quantities, decades, legal references, scores,
versions, IPv4, postal codes, street addresses.
Punctuation-aware (built for ASR output): `"сто гривень, будь ласка!"` -> `₴100, будь ласка!`,
`"нуль шістдесят сім, сто двадцять три, сорок п'ять, шістдесят сім"` -> `0671234567`

## Installation

```shell
brew install openfst   # needed to build pynini

export CPLUS_INCLUDE_PATH="/opt/homebrew/include:$CPLUS_INCLUDE_PATH"
export LIBRARY_PATH="/opt/homebrew/lib:$LIBRARY_PATH"

uv sync
```

## Usage

```python
from ukr import normalize

normalize("це трапилося дві тисячі дев'ятнадцятого числа")  # це трапилося 2019-го числа
normalize("мінус п'ять цілих одна десята відсотка")  # -5.1 %
normalize("двадцять дві тисячі сто один")  # 22101
normalize("сьома година двадцять п'ять хвилин")  # 07:25
```

The grammars are built lazily on the first call (a couple of seconds) and cached for the
lifetime of the process; subsequent calls take milliseconds. `normalize` is thread-safe.

### From command line

```shell
echo "це трапилося дві тисячі дев'ятнадцятого числа" | python -m ukr
# or, after `pip install ukr_itn`:
echo "це трапилося дві тисячі дев'ятнадцятого числа" | ukr-itn
```

```
Options:
  -h, --help     Show this help message and exit
  -j, --json     Return result as JSON
  -v, --verbose  Print original input and normalized to compare
  --version      Show version
```

Will return `це трапилося 2019-го числа`. Lines the grammar cannot parse are reported to
stderr and skipped (exit code 1).

### JSON output

For more advanced usage you can get json output

```python
from ukr import normalize

normalize("це трапилося дві тисячі дев'ятнадцятого числа", json=True)
# >>> '[{"word": "це"}, {"word": "трапилося"}, {"ordinal": "2019"}, {"word": "числа"}]'
```

## C++ library

The compiled grammars can be exported and used from C++ with plain OpenFST (no Python at
runtime):

```shell
uv run python -m ukr.export grammars_export
cmake -B cpp/build -S cpp && cmake --build cpp/build
echo "двадцять дві тисячі сто один" | ./cpp/build/ukr_itn_cli grammars_export  # 22101
```

See [cpp/README.md](cpp/README.md) for the library API.

## How it works

We have two kinds of FST: taggers and verbalizers.

This is a tagger:

```python
from ukr.wfst import get_normalizer, apply_fst_text

apply_fst_text("мінус п'ять цілих одна десята відсотка", get_normalizer().classify.fst)
```

will return `tokens { measure { negative: "true" integer_part: "5" fractional_part: "1" units: "%" } }`

And this is a verbalizer:

```python
from ukr.wfst import get_normalizer, apply_fst_text

apply_fst_text('tokens { measure { negative: "true" integer_part: "5" fractional_part: "1" units: "%" } }',
               get_normalizer().verbalize_final.fst)
```

will return `-5.1 %`

## Development

```shell
uv sync                # install deps (dev group included)
uv run pytest          # run tests
uv run ruff check .    # lint
uv build               # build sdist + wheel
```
