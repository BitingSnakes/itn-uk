"""Smoke-test byte-for-byte parity between the Python and C++ pipelines."""

from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

from ukr import normalize

CASES = (
    "двадцять дві тисячі сто один",
    "мінус п'ять цілих одна десята відсотка",
    "одна друга",
    "сто гривень, будь ласка!",
    "першого січня дві тисячі першого року",
    "сьома година двадцять п'ять хвилин",
    "нуль шістдесят сім, сто двадцять три, сорок п'ять, шістдесят сім",
    "іван крапка петренко собака джімейл крапка ком",
    "дев'ятнадцяте століття",
    "від п'яти до десяти відсотків",
    "дві години тридцять хвилин",
    "у вісімдесятих роках",
    "стаття п'ята частина друга",
    "з рахунком три нуль",
    "версії три крапка десять крапка один",
    "сто дев'яносто два крапка сто шістдесят вісім крапка один крапка один",
    "нуль один нуль тридцять",
    "вулиця миру будинок два корпус три квартира сорок",
    "Київ витратив СТО ГРИВЕНЬ",
    "мінус п’ять гривень",
    "двадцять\u00a0дві тисячі сто один",
    "двадцять\u2003дві тисячі сто один",
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("cli", type=Path)
    parser.add_argument("grammar_dir", type=Path)
    args = parser.parse_args()

    expected = [normalize(text) for text in CASES]
    completed = subprocess.run(
        [str(args.cli), str(args.grammar_dir)],
        input="".join(f"{text}\n" for text in CASES),
        text=True,
        capture_output=True,
        check=False,
    )
    actual = completed.stdout.splitlines()

    if completed.returncode != 0:
        print(completed.stderr, end="")
        return completed.returncode
    if len(actual) != len(expected):
        print(f"C++ returned {len(actual)} lines for {len(expected)} inputs")
        return 1

    mismatches = [
        (source, python_output, cpp_output)
        for source, python_output, cpp_output in zip(CASES, expected, actual)
        if python_output != cpp_output
    ]
    for source, python_output, cpp_output in mismatches:
        print(f"input:  {source}")
        print(f"python: {python_output}")
        print(f"c++:    {cpp_output}")
    if mismatches:
        return 1

    print(f"Python/C++ parity passed for {len(CASES)} representative inputs")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
