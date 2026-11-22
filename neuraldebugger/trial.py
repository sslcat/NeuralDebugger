"""Frozen v2 paired evaluation and local process supervision."""

import argparse
import ast
import csv
import json
import os
from pathlib import Path
import statistics
import subprocess
import sys
import time

from .corpus import LEGACY, V2, fixture_probes, observe, read_rows, sha
from .data import DATA, load
from .model import Engine
from .sandbox import Sandbox
from .schema import parse
from .settings import MODEL, REV, ROOT, PROTOCOL

RESULT = ROOT / "results/v2"
ADAPTER = ROOT / ".runs/v2-lora"
SETS = ("test", "independent")


def cases(name):
    if name not in SETS:
        raise ValueError(name)
    return load("test") if name == "test" else read_rows(name)


def identity():
    manifest = json.loads((V2 / "manifest.json").read_text())
    for name, entry in manifest["splits"].items():
        folder = DATA if name == "test" else V2
        if sha(folder / f"{name}.jsonl") != entry["sha256"]:
            raise ValueError("Split digest mismatch")
    if sha(DATA / "test.jsonl") != LEGACY:
        raise ValueError("Legacy drift")
    return dict(
        model=MODEL,
        revision=REV,
        manifest=sha(V2 / "manifest.json"),
        seed=PROTOCOL["seed"],
        device="NVIDIA GeForce RTX 4070 SUPER",
        files={
            p: sha(ROOT / p)
            for p in (
                "configs/protocol.json",
                "configs/lora.json",
                "neuraldebugger/model.py",
                "neuraldebugger/schema.py",
                "neuraldebugger/sandbox.py",
                "neuraldebugger/corpus.py",
                "neuraldebugger/trial.py",
            )
        },
    )


def score(raw, row, box):
    probes = fixture_probes(row)
    result = dict(invalid=True, category=False, passes=[False] * len(probes))
    try:
        diagnosis = parse(raw)
    except ValueError:
        return result
    result["category"] = diagnosis.category.casefold() == row["category"].casefold()
    try:
        tree = ast.parse(diagnosis.corrected_code)
        if not any(
            isinstance(n, ast.FunctionDef) and n.name == row["function"]
            for n in tree.body
        ):
            return result
    except (SyntaxError, ValueError, RecursionError):
        return result
    result["invalid"] = False
    result["passes"] = [observe(box, diagnosis.corrected_code, p)[0] for p in probes]
    return result


def evaluate(mode):
    import torch
    from transformers import set_seed

    set_seed(PROTOCOL["seed"])
    config = identity()
    box = Sandbox()
    adapter = (
        ADAPTER / (ADAPTER / "best.txt").read_text().strip()
        if mode == "adapter"
        else None
    )
    engine = Engine(adapter, strict=True)
    if engine.device != "cuda" or "4070 SUPER" not in torch.cuda.get_device_name():
        raise RuntimeError("Local GPU required")
    warm = read_rows("validation")[0]
    engine.predict(warm["buggy_code"], warm["traceback"])
    config.update(
        mode=engine.mode,
        dtype=str(engine.dtype),
        torch=torch.__version__,
        adapter_sha256=sha(adapter / "adapter_model.safetensors") if adapter else None,
    )
    out = RESULT / mode
    out.mkdir(parents=True, exist_ok=False)
    (out / "metadata.json").write_text(json.dumps(config, indent=2))
    for name in SETS:
        with (out / f"{name}.jsonl").open("x", encoding="utf8") as f:
            for case in cases(name):
                torch.cuda.synchronize()
                start = time.monotonic()
                raw = engine.predict(case["buggy_code"], case["traceback"])
                torch.cuda.synchronize()
                seconds = time.monotonic() - start
                record = dict(
                    id=case["id"], raw=raw, seconds=seconds, **score(raw, case, box)
                )
                f.write(json.dumps(record) + "\n")
                f.flush()
                print(mode, name, case["id"], round(seconds, 2), flush=True)


def bounded(stage, args, limit):
    env = dict(
        os.environ,
        ND_DEVICE="cuda",
        HF_HUB_OFFLINE="1",
        PYTHONUTF8="1",
        TRANSFORMERS_VERBOSITY="error",
    )
    exe = sys.executable
    if os.name == "nt" and sys.prefix != sys.base_prefix:
        exe = sys._base_executable
        env["__PYVENV_LAUNCHER__"] = sys.executable
    start = time.monotonic()
    fields = "timestamp,name,utilization.gpu,memory.used,memory.total"
    with (RESULT / f"{stage}-gpu.csv").open("x") as gpu:
        monitor = subprocess.Popen(
            ["nvidia-smi", "--query-gpu=" + fields, "--format=csv,nounits", "-l", "1"],
            stdout=gpu,
        )
        try:
            subprocess.run(
                [exe, "-u", "-m", *args], cwd=ROOT, env=env, check=True, timeout=limit
            )
        finally:
            monitor.terminate()
            monitor.wait(timeout=10)
    return time.monotonic() - start


def run():
    RESULT.mkdir(parents=True, exist_ok=False)
    identity()
    for stage, args, limit in [
        ("base", ["neuraldebugger.trial", "base"], 2400),
        ("train", ["neuraldebugger.train", "--expanded", "--out", str(ADAPTER)], 900),
        ("adapter", ["neuraldebugger.trial", "adapter"], 2400),
    ]:
        elapsed = bounded(stage, args, limit)
        (RESULT / f"{stage}-time.json").write_text(
            json.dumps(dict(wall_seconds=elapsed, timeout_seconds=limit))
        )
        if stage == "train":
            from tools.artifacts import verify

            best = ADAPTER / (ADAPTER / "best.txt").read_text().strip()
            verify(best)
            (RESULT / "loss.jsonl").write_bytes(
                (ADAPTER / "metrics.jsonl").read_bytes()
            )
            sizes = {
                p.parent.name: p.stat().st_size
                for p in sorted(ADAPTER.glob("epoch-*/adapter_model.safetensors"))
            }
            (RESULT / "checkpoints.json").write_text(
                json.dumps(
                    dict(
                        bytes=sizes,
                        selected=best.name,
                        sha256=sha(best / "adapter_model.safetensors"),
                    ),
                    indent=2,
                )
            )


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("action", choices=["run", "base", "adapter"])
    action = p.parse_args().action
    run() if action == "run" else evaluate(action)
