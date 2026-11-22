"""Masked prose review, paired program-level intervals, and complete case reports."""

import argparse
from collections import Counter
import csv
import json
import math
from pathlib import Path
import random
import secrets
import statistics as st
from itertools import chain

from .corpus import fixture_probes
from .schema import parse
from .trial import RESULT, SETS, cases, identity
from .settings import ROOT

METRICS = ("repair", "checks", "category", "invalid", "cause", "explanation", "seconds")


def read(path):
    return [json.loads(line) for line in path.read_text(encoding="utf8").splitlines()]


def paired(name):
    arms = [read(RESULT / m / f"{name}.jsonl") for m in ("base", "adapter")]
    ref = cases(name)
    if any([r["id"] for r in rows] != [r["id"] for r in ref] for rows in arms):
        raise ValueError("Missing, repeated or reordered benchmark case")
    meta = [
        json.loads((RESULT / m / "metadata.json").read_text())
        for m in ("base", "adapter")
    ]
    if (meta[0]["mode"], meta[1]["mode"]) != ("base", "adapter"):
        raise ValueError("Expected distinct model arms")
    for k in [*identity(), "dtype", "torch"]:
        if meta[0][k] != meta[1][k]:
            raise ValueError("Inconsistent benchmark configuration: " + k)
    return list(zip(ref, *arms, strict=True))


def answers(r):
    try:
        a = parse(r["raw"])
        return {"cause": a.root_cause, "explanation": a.explanation}
    except ValueError:
        return {"cause": "[unparseable]", "explanation": "[unparseable]"}


def packet():
    dest = RESULT / "masked.jsonl"
    keypath = ROOT / ".runs/v2-review-key.json"
    if dest.exists() or keypath.exists():
        raise FileExistsError("Review packet already exists")
    keys = {}
    with dest.open("x", encoding="utf8") as f:
        for s in SETS:
            for case, base, adapter in paired(s):
                order = ["base", "adapter"]
                if secrets.randbelow(2):
                    order.reverse()
                keys[case["id"]] = order
                options = {"base": base, "adapter": adapter}
                row = dict(
                    id=case["id"],
                    split=s,
                    reference=case["root_cause"],
                    repair=case["explanation"],
                    code=case["buggy_code"],
                    A=answers(options[order[0]]),
                    B=answers(options[order[1]]),
                )
                f.write(json.dumps(row) + "\n")
    keypath.write_text(json.dumps(keys, indent=2))


def metrics(rows):
    return dict(
        repair=st.mean(all(r["passes"]) for r in rows),
        checks=sum(sum(r["passes"]) for r in rows)
        / sum(len(r["passes"]) for r in rows),
        category=st.mean(r["category"] for r in rows),
        invalid=st.mean(r["invalid"] for r in rows),
        cause=st.mean(r["cause"] for r in rows),
        explanation=st.mean(r["explanation"] for r in rows),
        seconds=st.median(r["seconds"] for r in rows),
    )


def wilson(n, k):
    z = 1.95996398454
    p = k / n
    d = 1 + z * z / n
    center = (p + z * z / (2 * n)) / d
    margin = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return [max(0, center - margin), min(1, center + margin)]


def comparison(pairs, rounds=3000):
    rng = random.Random(9428)
    before, after = [metrics(rows) for rows in zip(*pairs)]
    draws = {k: [] for k in METRICS}
    for _ in range(rounds):
        sample = rng.choices(pairs, k=len(pairs))
        a, b = [metrics(rows) for rows in zip(*sample)]
        for k in METRICS:
            draws[k].append(b[k] - a[k])
    changes = {}
    for k in METRICS:
        delta = after[k] - before[k]
        seq = sorted(draws[k])
        changes[k] = dict(
            base=before[k],
            adapter=after[k],
            delta=delta,
            relative=delta / before[k] if before[k] else None,
            paired_95=[seq[int(0.025 * rounds)], seq[math.ceil(0.975 * rounds) - 1]],
        )
        if k in ("repair", "category", "invalid"):
            changes[k]["base_wilson_95"] = wilson(
                len(pairs), round(before[k] * len(pairs))
            )
            changes[k]["adapter_wilson_95"] = wilson(
                len(pairs), round(after[k] * len(pairs))
            )
    return changes


def finish():
    keypath = ROOT / ".runs/v2-review-key.json"
    if not keypath.exists():
        keypath = RESULT / "review-key.json"
    keys = json.loads(keypath.read_text())
    marks = read(RESULT / "ratings.jsonl")
    ratings = {r["id"]: r for r in marks}
    if len(ratings) != len(marks) or set(ratings) != set(keys):
        raise ValueError("Incomplete review")
    summary = {}
    display = [
        "# Local paired evaluation",
        "",
        "I scored raw outputs from the RTX 4070 SUPER. The independent suite is the primary outcome. Scores for cause and explanation come from one masked AI-assisted reviewer on a 0–2 scale. All intervals below resample paired programs.",
        "",
    ]
    reports = ["# All paired cases", ""]
    for s in SETS:
        pairs = []
        groups = {}
        failures = []
        for case, base, adapter in paired(s):
            cid = case["id"]
            rate = ratings[cid]
            order = keys[cid]
            reports += [
                "## " + cid,
                "",
                case["root_cause"],
                "",
                "```python",
                case["buggy_code"],
                "```",
                "",
                "```text",
                case["traceback"],
                "```",
                "",
            ]
            for label, row in [("base", base), ("adapter", adapter)]:
                tag = "AB"[order.index(label)]
                scores = rate[tag]
                if len(scores) != 2 or not all(
                    type(q) is int and 0 <= q <= 2 for q in scores
                ):
                    raise ValueError(cid)
                row["cause"], row["explanation"] = scores
                reports += [
                    f"**{label.title()}** — {sum(row['passes'])}/{len(row['passes'])} behavioral checks; cause {scores[0]}/2, explanation {scores[1]}/2.",
                    "",
                    "`````text",
                    row["raw"],
                    "`````",
                    "",
                ]
                missed = [
                    p
                    for p, ok in zip(fixture_probes(case), row["passes"], strict=True)
                    if not ok
                ]
                if missed:
                    reports += ["Failed inputs and expected values", "", "```text"]
                    reports += [p["expr"] + " -> " + p["want"] for p in missed]
                    reports += ["```", ""]
            reports += ["Review: " + rate["note"], ""]
            pair = (base, adapter)
            pairs.append(pair)
            groups.setdefault(case["category"], []).append(pair)
            if (
                not (all(base["passes"]) and all(adapter["passes"]))
                or base["invalid"]
                or adapter["invalid"]
            ):
                failures.append(cid)
        changes = comparison(pairs)
        detail = {
            g: dict(
                n=len(items),
                base=metrics([p[0] for p in items]),
                adapter=metrics([p[1] for p in items]),
            )
            for g, items in groups.items()
        }
        summary[s] = dict(
            n=len(pairs),
            metrics=changes,
            by_category=detail,
            patch_failures=failures,
            improved=[
                case["id"]
                for case, (a, b) in zip(cases(s), pairs)
                if not all(a["passes"]) and all(b["passes"])
            ],
            regressed=[
                case["id"]
                for case, (a, b) in zip(cases(s), pairs)
                if all(a["passes"]) and not all(b["passes"])
            ],
        )
        display += [
            f"## {s.title()} ({len(pairs)} programs)",
            "",
            "| Metric | Base | Adapter | Change | Paired 95% interval for change |",
            "|---|---:|---:|---:|---:|",
        ]
        for k, v in changes.items():
            lo, hi = v["paired_95"]
            display.append(
                f"| {k} | {v['base']:.3f} | {v['adapter']:.3f} | {v['delta']:+.3f} | [{lo:+.3f}, {hi:+.3f}] |"
            )
        display += [
            "",
            "| Gold category | n | Patches passing (base → adapter) | Categories correct | Mean cause | Mean explanation |",
            "|---|---:|---:|---:|---:|---:|",
        ]
        for g, d in sorted(detail.items()):
            n = d["n"]
            a = d["base"]
            b = d["adapter"]
            display.append(
                f"| {g} | {n} | {round(n * a['repair'])} → {round(n * b['repair'])} | {round(n * a['category'])} → {round(n * b['category'])} | {a['cause']:.2f} → {b['cause']:.2f} | {a['explanation']:.2f} → {b['explanation']:.2f} |"
            )
        display += [
            "",
            "Cases failing at least one behavioral probe in either arm: "
            + (", ".join(failures) or "none")
            + ".",
            "",
        ]
    (RESULT / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf8")
    (RESULT / "case-reports.md").write_text("\n".join(reports), encoding="utf8")
    (RESULT / "comparison.md").write_text("\n".join(display), encoding="utf8")
    (RESULT / "review-key.json").write_text(json.dumps(keys, indent=2))


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("action", choices=["packet", "finish"])
    packet() if p.parse_args().action == "packet" else finish()
