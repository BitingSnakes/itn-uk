# ukr_itn — C++ library

C++ Inverse Text Normalization for Ukrainian built on plain [OpenFST](https://www.openfst.org)
(no pynini needed at runtime). It consumes grammars exported from the Python package and
reproduces the same pipeline (tag → reorder → verbalize, shortest path at each step);
output is byte-for-byte identical to `ukr.normalize`.

## 1. Export the grammars (one-time, needs Python + pynini)

```shell
uv run python -m ukr.export grammars_export
```

This writes `ukr_itn_tagger.fst`, `ukr_itn_verbalizer.fst` (plain OpenFST binaries,
loadable with `fst::StdVectorFst::Read`) and `ukr_itn.far` (both grammars in one FAR
archive, keys `TAGGER` / `VERBALIZER`).

## 2. Build

```shell
brew install openfst cmake   # macOS; on Debian/Ubuntu: apt install libfst-dev cmake
cmake -B build -S cpp
cmake --build build
```

Produces `libukr_itn.a` and the `ukr_itn_cli` demo binary.

## 3. Use

Command line:

```shell
echo "двадцять дві тисячі сто один" | ./build/ukr_itn_cli grammars_export
# 22101
```

As a library:

```cpp
#include "ukr_itn/ukr_itn.h"

std::string error;
auto itn = ukr_itn::InverseNormalizer::FromFiles(
    "grammars_export/ukr_itn_tagger.fst",
    "grammars_export/ukr_itn_verbalizer.fst", &error);

std::string out;
if (itn->Normalize("сьома година двадцять п'ять хвилин", &out)) {
  // out == "07:25"
}
// or, never fails:
std::string out2 = itn->NormalizeOrPassthrough("будь-який текст");
```

Link against `ukr_itn` and OpenFST (`-lfst`). The normalizer is immutable after
construction; `Normalize` is safe to call concurrently from multiple threads.
