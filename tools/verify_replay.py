"""Compare a complete local replay to the archived, paired held-out responses."""

import argparse
from pathlib import Path

from neuraldebugger.hybrid_trial import ARMS, OUT, SETS, cases
from neuraldebugger.report import read


def verify(directory):
    accepted = True
    for split in SETS:
        ids = [r["id"] for r in cases(split)]
        repairs = {}
        for arm in ARMS:
            expected = read(OUT / arm / f"{split}.jsonl")
            actual = read(directory / arm / f"{split}.jsonl")
            if any([r["id"] for r in rows] != ids for rows in (expected, actual)):
                raise ValueError(f"Missing, duplicated or reordered cases in {arm}/{split}")
            repairs[arm] = [r["repair_raw"] for r in actual]
            different = []
            for a, b in zip(actual, expected, strict=True):
                fields = ("repair_raw", "classifier_raw", "classifier_label", "conditioned",
                          "fallback", "raw", "invalid", "category", "passes")
                if any(a[k] != b[k] for k in fields):
                    different.append(a["id"])
            accepted &= not different
            print(f"{split} {arm}: {len(ids)-len(different)}/{len(ids)} exact responses and scores")
            if different:
                print("Changed cases:", ", ".join(different))
        same = sum(a == b for a, b in zip(repairs["base"], repairs["hybrid-display"], strict=True))
        print(f"{split} display-only: {same}/{len(ids)} identical base repair texts")
        accepted &= same == len(ids)
    return accepted


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    raise SystemExit(0 if verify(parser.parse_args().directory) else 1)
