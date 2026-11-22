"""Build a masked prose packet and summarize paired hybrid experiment outputs."""

import argparse
from collections import defaultdict
import csv
import hashlib
import json
import random
import statistics as st

from .hybrid_trial import ARMS, OUT
from .report import answers, comparison, metrics, read
from .schema import parse
from .trial import RESULT, SETS, cases


def prose_key(case_id, prose):
    return hashlib.sha256(
        json.dumps(
            [case_id, prose["cause"], prose["explanation"]], ensure_ascii=False
        ).encode()
    ).hexdigest()


def previous_ratings():
    marks = {r["id"]: r for r in read(RESULT / "ratings.jsonl")}
    evidence = defaultdict(set)
    for r in read(RESULT / "masked.jsonl"):
        for tag in "AB":
            evidence[prose_key(r["id"], r[tag])].add(tuple(marks[r["id"]][tag]))
    return {k: list(v)[0] for k, v in evidence.items() if len(v) == 1}


def load_arms(split):
    gold = cases(split)
    arms = {a: read(OUT / a / f"{split}.jsonl") for a in ARMS}
    for a, rows in arms.items():
        if [r["id"] for r in rows] != [r["id"] for r in gold]:
            raise ValueError(f"Missing, reordered or duplicate predictions in {a}")
    return gold, arms


def packet():
    known = previous_ratings()
    pending = {}
    for split in SETS:
        gold, arms = load_arms(split)
        for records in arms.values():
            for r, c in zip(records, gold, strict=True):
                prose = answers(r)
                k = prose_key(c["id"], prose)
                if k not in known and prose["cause"] != "[unparseable]":
                    pending[k] = dict(
                        key=k,
                        id=c["id"],
                        reference=c["root_cause"],
                        reference_fix=c["explanation"],
                        buggy_code=c["buggy_code"],
                        **prose,
                    )
    rows = list(pending.values())
    random.SystemRandom().shuffle(rows)
    with (OUT / "masked.jsonl").open("x", encoding="utf8") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")
    print("Novel distinct prose pairs:", len(rows))


def verified_marks():
    known = previous_ratings()
    packet_rows = read(OUT / "masked.jsonl")
    ratings = read(OUT / "ratings.jsonl")
    if len(ratings) != len(packet_rows):
        raise ValueError("Incomplete review")
    for r, p in zip(ratings, packet_rows, strict=True):
        s = r["scores"]
        if (
            r["key"] != p["key"]
            or len(s) != 2
            or not all(type(v) is int and 0 <= v <= 2 for v in s)
        ):
            raise ValueError("Invalid or reordered rating")
        known[r["key"]] = s
    return known


def repair_category(r):
    try:
        return parse(r["repair_raw"]).category
    except ValueError:
        return None


def summarize():
    known = verified_marks()
    result = {}
    notes = [
        "# Hybrid evaluation",
        "",
        "I reran all four arms on the local RTX 4070 SUPER. Repair counts require every behavioral probe to pass. I scored the raw diagnosis prose on a 0–2 scale. I count a missing or unparseable diagnosis as a classification miss and score a parseable category even if its program is unusable. The standalone classifier is also scored before repair parsing.",
        "",
    ]
    review = ["# Paired case ledger", ""]
    for split in SETS:
        gold, arms = load_arms(split)
        n = len(gold)
        report = {}
        notes.extend(
            [
                f"## {'Legacy' if split == 'test' else 'Independent'} · {n} programs",
                "",
                "| Configuration | Complete repairs | Passing probes | Category correct | Mean cause | Mean explanation | Invalid | Median seconds | Peak allocated GiB | Peak reserved GiB |",
                "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
            ]
        )
        for arm, rows in arms.items():
            for row in rows:
                prose = answers(row)
                s = (
                    (0, 0)
                    if prose["cause"] == "[unparseable]"
                    else known[prose_key(row["id"], prose)]
                )
                row["cause"], row["explanation"] = s
            m = metrics(rows)
            by_category = {}
            for cat in sorted({c["category"] for c in gold}):
                group = [r for r, c in zip(rows, gold) if c["category"] == cat]
                by_category[cat] = dict(n=len(group), **metrics(group))
            allocated = max(r["peak_allocated"] for r in rows)
            reserved = max(r["peak_reserved"] for r in rows)
            counts = dict(
                repairs=sum(all(r["passes"]) for r in rows),
                probes=sum(sum(r["passes"]) for r in rows),
                total_probes=sum(len(r["passes"]) for r in rows),
                categories=sum(r["category"] for r in rows),
                invalid=sum(r["invalid"] for r in rows),
            )
            report[arm] = dict(
                metrics=m,
                counts=counts,
                peak_allocated_bytes=allocated,
                peak_reserved_bytes=reserved,
                by_category=by_category,
            )
            notes.append(
                f"| {arm} | {counts['repairs']}/{n} | {counts['probes']}/{counts['total_probes']} | {counts['categories']}/{n} | {m['cause']:.2f} | {m['explanation']:.2f} | {counts['invalid']}/{n} | {m['seconds']:.2f} | {allocated / 2**30:.3f} | {reserved / 2**30:.3f} |"
            )
        for arm in ARMS[1:]:
            report[arm]["paired_vs_base"] = comparison(
                list(zip(arms["base"], arms[arm], strict=True))
            )
        routes = []
        for i, c in enumerate(gold):
            b, a, d, h = (arms[m][i] for m in ARMS)
            if d["classifier_label"] != h["classifier_label"]:
                raise ValueError(
                    "Classifier disagreement between equivalent first stages"
                )
            info = dict(
                id=c["id"],
                gold=c["category"],
                classifier=d["classifier_label"],
                classifier_correct=d["classifier_label"] == c["category"],
                conditioned=h["conditioned"],
                repairer_category=repair_category(h),
                base_raw_unchanged=b["repair_raw"] == d["repair_raw"],
                base_pass=all(b["passes"]),
                adapter_pass=all(a["passes"]),
                adapter_category_correct=a["category"],
                display_pass=all(d["passes"]),
                conditioned_pass=all(h["passes"]),
                display_probes=d["passes"],
                conditioned_probes=h["passes"],
                display_fallback=d["fallback"],
                conditioned_fallback=h["fallback"],
            )
            routes.append(info)
            review.extend(
                [
                    f"## {c['id']}",
                    "",
                    f"Gold category: {c['category']}. Classifier prediction: {d['classifier_label']}.",
                    "",
                    "| Arm | Checks | Reported category correct | Cause | Explanation |",
                    "|---|---:|---:|---:|---:|",
                ]
            )
            for arm in ARMS:
                r = arms[arm][i]
                review.append(
                    f"| {arm} | {sum(r['passes'])}/{len(r['passes'])} | {r['category']} | {r['cause']}/2 | {r['explanation']}/2 |"
                )
            review.append("")
        report["routing"] = routes
        report["classifier_stage"] = dict(
            correct=sum(r["classifier_correct"] for r in routes),
            valid=sum(r["classifier"] is not None for r in routes),
            programs=n,
        )
        notes += [
            "",
            f"The category-only decode matched {sum(r['classifier_correct'] for r in routes)}/{n} gold categories. The display-only repair text matched the standalone base output byte-for-byte on {sum(r['base_raw_unchanged'] for r in routes)}/{n}.",
            "",
            "| Classifier result | Programs | Display repairs | Conditioned repairs | Gains | Losses |",
            "|---|---:|---:|---:|---:|---:|",
        ]
        for correct in (True, False):
            g = [r for r in routes if r["classifier_correct"] == correct]
            notes.append(
                f"| {'Correct' if correct else 'Incorrect or missing'} | {len(g)} | {sum(r['display_pass'] for r in g)} | {sum(r['conditioned_pass'] for r in g)} | {sum(not r['display_pass'] and r['conditioned_pass'] for r in g)} | {sum(r['display_pass'] and not r['conditioned_pass'] for r in g)} |"
            )
        ci = report["hybrid-conditioned"]["paired_vs_base"]["repair"]["paired_95"]
        notes += [
            "",
            f"The conditioned-minus-base repair-rate difference has a paired 95% bootstrap interval of [{ci[0] * 100:+.1f}, {ci[1] * 100:+.1f}] percentage points.",
            "",
        ]
        result[split] = report
    pilot = json.loads((OUT / "validation/repair-pilot.json").read_text())
    wrong = json.loads((OUT / "validation/wrong-hint.json").read_text())
    control = []
    for w in wrong:
        d, h = [
            next(r for r in pilot if r["id"] == w["id"] and r["arm"] == arm)
            for arm in ARMS[2:]
        ]
        if h["label"] != w["gold"]:
            raise ValueError("Control expected correct validation hint")
        control.append(
            dict(
                id=w["id"],
                gold=w["gold"],
                wrong=w["forced_hint"],
                display=d["passes"],
                correct_hint=h["passes"],
                wrong_hint=w["passes"],
            )
        )
    result["wrong_hint_control"] = control
    notes += [
        "## Deliberately wrong validation hints",
        "",
        "| Validation program | No hint | Correct hint | Wrong hint |",
        "|---|---:|---:|---:|",
    ]
    for r in control:
        notes.append(
            "| "
            + r["id"]
            + " | "
            + " | ".join(
                f"{sum(r[k])}/{len(r[k])}"
                for k in ("display", "correct_hint", "wrong_hint")
            )
            + " |"
        )
    telemetry = {}
    for arm in ARMS:
        rows = list(csv.reader((OUT / f"{arm}-gpu.csv").read_text().splitlines()))[1:]
        samples = [
            (int(r[2]), int(r[3]))
            for r in rows
            if len(r) == 5 and r[2].strip().isdigit()
        ]
        telemetry[arm] = dict(
            samples=len(samples),
            mean_whole_card_util_pct=st.mean(x[0] for x in samples),
            peak_whole_card_used_mib=max(x[1] for x in samples),
        )
    result["whole_card"] = telemetry
    notes += [
        "", "## Device-wide telemetry", "",
        "I sampled the entire GPU once per second, including model loading, behavioral scoring and activity from other applications. The suite tables above give process-specific PyTorch peaks during warmed inference.", "",
        "| Configuration | Samples | Mean GPU utilization | Peak memory used, MiB |",
        "|---|---:|---:|---:|",
    ]
    for arm, values in telemetry.items():
        notes.append(f"| {arm} | {values['samples']} | {values['mean_whole_card_util_pct']:.1f}% | {values['peak_whole_card_used_mib']} |")
    notes += ["", "I used one masked, AI-assisted reviewer for root cause and explanation. I reused scores for identical prose on the same program. The summary file contains results by category and paired intervals for each metric. [Machine-readable summary](summary.json) · [Every held-out case](all-cases.md)", ""]

    (OUT / "summary.json").write_text(json.dumps(result, indent=2), encoding="utf8")
    (OUT / "comparison.md").write_text("\n".join(notes).rstrip() + "\n", encoding="utf8")
    (OUT / "all-cases.md").write_text("\n".join(review), encoding="utf8")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("action", choices=["packet", "summarize"])
    packet() if p.parse_args().action == "packet" else summarize()
