# Changelog

### v0.1.9

- Richer grammar data:
    - Fixed DATE grammar for July — `month.tsv` contained «ли́пень» with a combining accent,
      so `"п'ятого липня"` was silently left unnormalized; now -> `5 липня`.
    - MEASURE: added length (`км`, `м`, `см`, `мм`), mass (`кг`, `г`, `т`), volume (`л`, `мл`),
      area (`га`), time (`с`) units and colloquial «процент» (full case paradigms), e.g.
      `"сто двадцять кілометрів"` -> `120 км`, `"мінус п'ять цілих три десятих кілограма"` -> `-5.3 кг`.
    - MONEY: added euro (`"два євро п'ятдесят євроцентів"` -> `€2.50`) and pound sterling
      (`"п'ять фунтів стерлінгів"` -> `£5`, `"два фунти двадцять пенсів"` -> `£2.20`).
    - The money verbalizer now derives accepted currency symbols from the data files
      instead of a hardcoded `$`/`₴` list.
- Production hardening:
    - Grammars are now built lazily on first use — `import ukr` is instant.
    - New public API: `from ukr import normalize, InverseNormalizer` (old `ukr.wfst` imports still work).
    - `normalize` validates input (raises `TypeError`/`ValueError` on non-string/empty input).
    - New `ukr-itn` console script (equivalent to `python -m ukr`); the CLI no longer crashes on unparseable lines — it reports them to stderr and continues.
    - Packaging: proper build backend, grammar data bundled in wheels, `py.typed` marker, Python >= 3.9.
    - Dev tooling: `ruff` lint (clean), expanded test suite (public API + CLI).
- New `python -m ukr.export` command exports the compiled tagger/verbalizer FSTs (`.fst`/`.far`) for reuse outside Python.
- New C++ library in `cpp/` (`ukr_itn`) that performs ITN with plain OpenFST using the exported FSTs — see `cpp/README.md`.

### v0.1.8

- Added TIME class, some examples:
    - `"сьома година двадцять п'ять хвилин"` -> `'07:25'`
    - `"о пів на десяту"` -> `'09:30'`
    - `"пів на третю"` -> `'02:30'`
    - `"чверть на одинадцяту"` -> `'10:15'`
    - `"за чверть одинадцята"` -> `'10:45'`
    - `"п'ять хвилин на дванадцяту"` -> `'11:05'`
    - `"дванадцята нуль нуль"` -> `'12:00'`
    - `"одинадцята нуль шість"` -> `'11:06'`
    - `"шоста сорок три"` -> `'06:43'`
- Defined new method `normalize` which should be used istead of `apply_fst_text` in production code.
  The reason is we need additional code to process some non-deterministic cases like for time class (for example minutes goes before hours).

### v0.1.7

- Added DATE class:
    - `"першого січня дві тисячі першого року"` -> `1 січня 2001 року'`
    - `"першого січня"` -> `1 січня'`
    - `"січень дві тисячі першого рок у"` -> `січень 2001 року'`
    - `"січень дві тисячі першого"` -> `січень 2001'`
    - `"дві тисячі першого рік"` -> `2001 рік'`
    - `"дев'ятсот сорок п'ятий рік до нашої ери"` -> `945 рік до н. е.'`
- Added JSON option for command line

### v0.1.6

- Added command line execution mode: `echo "це трапилося дві тисячі дев'ятнадцятого числа" | python -m ukr`
- Fixed bug with single digits, like `"один одного"` (but was `"1 1"`).
  Please note: single digit will normalize as written, like one -> one, two - two, ..., but eleven -> 11, twelve -> 12