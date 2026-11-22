"""Paired case bootstrap. Ratios and medians are recalculated in every resample."""

import argparse
import json
import random
from pathlib import Path

from .evaluate import summarize
from .settings import PROTOCOL


def read(folder):
    rows = [
        json.loads(x) for x in (folder / "predictions.jsonl").read_text().splitlines()
    ]
    return json.loads((folder / "metadata.json").read_text()), rows


def compare(base, tuned):
    a, x = read(base)
    b, y = read(tuned)
    if a["mode"] != "base" or b["mode"] != "adapter":
        raise ValueError("Expected base and adapter results")
    for field in (
        "model",
        "revision",
        "test",
        "protocol",
        "evaluator",
        "sandbox",
        "inference",
        "dtype",
        "device",
        "torch",
    ):
        if a[field] != b[field]:
            raise ValueError("Incompatible runs: " + field)
    from .data import load

    ids = [row["id"] for row in load("test")]
    if any([row["id"] for row in group] != ids for group in (x, y)):
        raise ValueError("Incomplete or reordered paired cases")
    rng = random.Random(PROTOCOL["seed"])
    before, after = summarize(x), summarize(y)
    changes = {k: [] for k, v in before.items() if v is not None}
    for _ in range(2000):
        sample = rng.choices(range(len(x)), k=len(x))
        left, right = (summarize([group[i] for i in sample]) for group in (x, y))
        for k in changes:
            changes[k].append(right[k] - left[k])
    metrics = {}
    for k in changes:
        delta = after[k] - before[k]
        draws = sorted(changes[k])
        metrics[k] = dict(
            base=before[k],
            adapter=after[k],
            delta=delta,
            relative=delta / before[k] if before[k] else None,
            paired_95=[draws[49], draws[1949]],
        )
    return {
        "metrics": metrics,
        "all_pairs": [
            dict(id=i, base=l["scores"], adapter=r["scores"])
            for i, l, r in zip(ids, x, y, strict=True)
        ],
    }


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("base", type=Path)
    p.add_argument("adapter", type=Path)
    args = p.parse_args()
    print(json.dumps(compare(args.base, args.adapter), indent=2))
