# Changelog

### v0.2.0

- JSON output now correctly escapes quotes, backslashes, control characters, and Unicode
  pass-through tokens, so `json=True` always returns syntactically valid JSON.
- Added orthographic preprocessing for uppercase input and the three common Ukrainian
  apostrophes (`'`, `’`, `ʼ`) while preserving original spelling/case in ordinary words.
- Added negative money normalization (`"мінус п'ять гривень"` -> `-₴5`).
- Fixed standalone thousandths (`"сім тисячних"` -> `0.007`) being misclassified as an ordinal.
- Constrained clock hours, minutes, calendar days, and IPv4 octets to valid numeric ranges.
- Hardened the C++ runtime with immutable thread-safe FSTs, UTF-8 validation, Python-equivalent
  Unicode whitespace handling, safe null-output behavior, native tests, and installable CMake targets.
- Added Python/C++ CI, distribution validation, representative parity checks, and C++ sources
  to the source distribution.

### v0.1.9

- Time & duration:
    - Time ranges (the «години» word is required): `"з дев'ятої до вісімнадцятої години"` -> `з 09:00 до 18:00`.
    - Durations: `"дві години тридцять хвилин"` -> `2 год 30 хв`, `"сорок хвилин"` -> `40 хв`;
      time-of-day idioms («п'ять хвилин на дванадцяту») are untouched.
    - Half-quantities: `"півтори години"` -> `1.5 год`, `"пів кілограма"` / `"півгодини"` -> `0.5 кг` / `0.5 год`.
- Date ranges (a month is required): `"з першого по п'яте січня"` -> `з 1 по 5 січня`.
- Decades: `"дев'яності роки"` -> `90-ті роки`, `"у вісімдесятих роках"` -> `у 80-х роках`.
- Legal/document references (keyword-gated, chainable):
  `"стаття п'ята частина друга"` -> `ст. 5 ч. 2`, `"сторінка сто двадцять"` -> `с. 120`,
  `"параграф третій"` -> `§ 3` (also `п.`, `пп.`, `розд.`, `гл.`, `абз.`).
- Sports scores gated on «рахунок»: `"з рахунком три нуль"` -> `з рахунком 3:0`.
- Version numbers gated on «версія»: `"версії три крапка десять крапка один"` -> `версії 3.10.1`.
- IPv4 addresses (exactly four dotted groups):
  `"сто дев'яносто два крапка сто шістдесят вісім крапка один крапка один"` -> `192.168.1.1`.
- New ELECTRONIC class — e-mail and web addresses as dictated, with KMU-2010
  romanization of free-form parts and a provider/TLD vocabulary:
  `"іван крапка петренко собака джімейл крапка ком"` -> `ivan.petrenko@gmail.com`,
  `"адмін собака укрнет"` -> `admin@ukr.net`, `"ве ве ве крапка приклад крапка юей"` -> `www.pryklad.ua`.
  Requires «собака» (e-mail) or «ве ве ве» (URL), so ordinary text never matches.
- Roman-numeral centuries and millennia (Ukrainian typographic convention):
  `"дев'ятнадцяте століття"` -> `XIX століття`, `"третього тисячоліття"` -> `III тисячоліття`.
- «номер» + number -> `№`: `"під номером двадцять два"` -> `під № 22`.
- Numeric ranges: `"від п'яти до десяти відсотків"` -> `5–10 %`,
  `"дві-три години"` -> `2–3 год`, `"п'ять-шість кілометрів"` -> `5–6 км`.
  Duration units («год», «хв») are recognised only inside ranges, so the time-of-day
  grammar is unaffected.
- Postal codes: zero-leading five-digit sequences, `"нуль один нуль тридцять"` -> `01030`.
- Street addresses (house number required to trigger):
  `"вулиця шевченка будинок п'ять квартира три"` -> `вул. шевченка, буд. 5, кв. 3`.
- New TELEPHONE class (ASR-oriented):
    - Ukrainian phone numbers dictated with the trunk «нуль» or international
      «плюс три вісім нуль» / «плюс тридцять вісім нуль» prefix, spoken as any mix of
      single digits, teens, tens and hundreds groups:
      `"нуль шістдесят сім сто двадцять три сорок п'ять шістдесят сім"` -> `0671234567`,
      `"плюс три вісім нуль шістдесят сім один два три чотири п'ять шість сім"` -> `+380671234567`.
    - ASR-inserted commas between dictated groups are consumed.
    - The match is constrained to the exact Ukrainian format (prefix + nine digits),
      so ordinary numbers never collapse into phone numbers.
- New FRACTION class:
    - `"одна друга"` -> `1/2`, `"дві третіх"` / `"дві треті"` -> `2/3`, `"три чверті"` -> `3/4`,
      `"мінус три двадцять п'ятих"` -> `-3/25`.
    - Powers of ten (`"одна десята"`) remain decimals; time phrases with «чверть» are unaffected.
- Punctuation-aware normalization:
    - Punctuation (`, . ! ? ; : … ( ) « »`) no longer blocks matches — it is split into
      standalone tokens before tagging and re-attached after verbalization, e.g.
      `"сто гривень, будь ласка!"` -> `₴100, будь ласка!`. Hyphens and apostrophes are
      treated as word-internal. The C++ library mirrors this behaviour exactly.
- Extended coverage:
    - MEASURE: speed (`"шістдесят кілометрів на годину"` -> `60 км/год`, `м/с`),
      temperature (`"двадцять п'ять градусів за цельсієм"` -> `25 °C`, bare degrees -> `°`),
      data sizes (`Б`, `КБ`, `МБ`, `ГБ`, `ТБ`), power & electricity (`Вт`, `кВт`, `кВт·год`, `А`, `В`),
      frequency (`Гц`, `кГц`, `МГц`, `ГГц`), plus `дБ`, `ккал`, `кал`, `мг` — 380 unit forms total,
      validated to be mutually unambiguous.
    - MONEY: added ₽ (рубль), zł (злотий), ¥ (єна); the tagger now supports currencies
      without a minor unit.
    - MONEY: full world-currency inventory — CHF (франк, «швейцарських франків»),
      ¥ юань, ₹ рупія, ₪ шекель, ₸ тенге, ฿ бат, ₺ ліра, R$ реал, ₩ вон, AED дирхам,
      ₿ біткоїн/біткойн, ₾ ларі, SEK/CZK/NOK/DKK («шведських крон», …),
      C$/A$ («канадських доларів», «австралійських доларів») — 256 spoken forms,
      validated mutually unambiguous. KRW accepts only «вон», never the pronouns
      «вона»/«вони».
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
