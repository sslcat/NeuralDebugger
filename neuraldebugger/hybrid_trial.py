"""Run local validation, freeze its selection, and compare four measured inference arms."""

import argparse
import json
from pathlib import Path
import statistics
import time

from .corpus import read_rows, sha
from .hybrid import CONFIG, HYBRIDS, Pipeline
from .sandbox import Sandbox
from .settings import ROOT, PROTOCOL
from .trial import ADAPTER, SETS, cases, identity, score

OUT = ROOT / "results/hybrid"
ARMS = ("base", "adapter", *HYBRIDS)


def write(path, data):
    with path.open("x", encoding="utf8") as f:
        json.dump(data, f, indent=2)


def engine(mode, strategy=None):
    import torch
    from transformers import set_seed

    if (
        not torch.cuda.is_available()
        or "4070 SUPER" not in torch.cuda.get_device_name()
    ):
        raise RuntimeError("Local RTX 4070 SUPER required")
    set_seed(PROTOCOL["seed"])
    checkpoint = ADAPTER / "epoch-3"
    if sha(checkpoint / "adapter_model.safetensors") != CONFIG["adapter_sha256"]:
        raise ValueError("Adapter checksum mismatch")
    p = Pipeline(mode, checkpoint, strict=True, strategy=strategy)
    if p.engine.device != "cuda":
        raise RuntimeError("CUDA required")
    return p


def validation():
    directory = OUT / "validation"
    directory.mkdir(parents=True, exist_ok=False)
    rows = read_rows("validation")
    p = engine("hybrid-display", "training-prefix")
    stats = {}
    for strategy in ("category-only", "training-prefix"):
        p.classify(rows[0]["buggy_code"], rows[0]["traceback"], strategy)
        guesses = []
        for r in rows:
            t = time.perf_counter()
            raw, label = p.classify(r["buggy_code"], r["traceback"], strategy)
            guesses.append(
                dict(
                    id=r["id"],
                    raw=raw,
                    label=label,
                    correct=label == r["category"],
                    seconds=time.perf_counter() - t,
                )
            )
        write(directory / f"{strategy}.json", guesses)
        stats[strategy] = dict(
            correct=sum(g["correct"] for g in guesses),
            valid=sum(g["label"] is not None for g in guesses),
            n=len(rows),
        )
    # Ties favor the original supervised prompt.
    selected = max(
        stats,
        key=lambda k: (stats[k]["correct"], stats[k]["valid"], k == "training-prefix"),
    )
    write(
        ROOT / "configs/hybrid-selection.json",
        dict(strategy=selected, validation=stats),
    )
    p.strategy = selected
    box = Sandbox()
    # Exercise each distinct repair path on preselected validation positions.
    pilot = []
    for r in rows[::4]:
        for arm in HYBRIDS:
            p.mode = arm
            pred = p.predict(r["buggy_code"], r["traceback"])
            try:
                raw = pred.diagnosis().model_dump_json()
            except ValueError:
                raw = pred.repair_raw
            pilot.append(
                dict(
                    id=r["id"],
                    arm=arm,
                    raw=raw,
                    label=pred.classifier_label,
                    conditioned=pred.conditioned,
                    **score(raw, r, box),
                )
            )
    write(directory / "repair-pilot.json", pilot)
    print(stats, selected, flush=True)


def protocol():
    return dict(
        original=identity(),
        files={
            p: sha(ROOT / p)
            for p in (
                "configs/hybrid.json",
                "configs/hybrid-selection.json",
                "neuraldebugger/hybrid.py",
                "neuraldebugger/hybrid_trial.py",
            )
        },
    )


def evaluate(arm):
    import torch

    frozen = json.loads((OUT / "freeze.json").read_text())
    if frozen != protocol():
        raise ValueError("Hybrid protocol changed after freeze")
    p = engine(arm)
    box = Sandbox()
    out = OUT / arm
    out.mkdir(parents=True, exist_ok=False)
    warm = read_rows("validation")[0]
    p.predict(warm["buggy_code"], warm["traceback"])
    for split in SETS:
        with (out / f"{split}.jsonl").open("x", encoding="utf8") as f:
            for case in cases(split):
                torch.cuda.synchronize()
                torch.cuda.reset_peak_memory_stats()
                start = time.perf_counter()
                pred = p.predict(case["buggy_code"], case["traceback"])
                try:
                    result = pred.diagnosis().model_dump_json()
                except ValueError:
                    result = pred.repair_raw
                torch.cuda.synchronize()
                seconds = time.perf_counter() - start
                row = dict(
                    id=case["id"],
                    seconds=seconds,
                    peak_allocated=torch.cuda.max_memory_allocated(),
                    peak_reserved=torch.cuda.max_memory_reserved(),
                    raw=result,
                    **vars(pred),
                    **score(result, case, box),
                )
                f.write(json.dumps(row) + "\n")
                f.flush()
                print(arm, split, case["id"], round(seconds, 2), flush=True)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("action", choices=["validate", "freeze", *ARMS])
    action = p.parse_args().action
    if action == "validate":
        validation()
    elif action == "freeze":
        write(OUT / "freeze.json", protocol())
    else:
        evaluate(action)
