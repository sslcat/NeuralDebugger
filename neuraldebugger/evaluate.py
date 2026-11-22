"""Capture immutable raw predictions and score all cases, including failures."""
import argparse
import ast
import hashlib
import json
import re
import statistics
import time
from pathlib import Path

from .data import load
from .model import Engine
from .schema import parse
from .settings import MODEL, PROTOCOL, REV, ROOT

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def grade(case, raw, sandbox):
    result = dict(category=0, root_cause=0, explanation=0, reference_ast=0, invalid=1,
                  tests=len(case["checks"]), passed=None if sandbox is None else 0)
    try:
        answer = parse(raw)
    except ValueError:
        return result
    result["category"] = int(answer.category.casefold() == case["category"].casefold())
    def concepts(s):
        return all(any(re.search(term, s, re.I) for term in group) for group in case["anchors"])
    result["root_cause"] = int(concepts(answer.root_cause))
    # Two observable rubric items: mechanism in diagnosis and a distinct actionable explanation.
    action = re.search(r"\b(us(e|es|ing)|call\w*|return\w*|replac\w*|add\w*|chang\w*|check\w*|creat\w*|convert\w*|initializ\w*|ensur\w*|increment\w*|limit\w*|unpack\w*)\b", answer.explanation, re.I)
    result["explanation"] = result["root_cause"] + int(bool(action) and answer.explanation != answer.root_cause)
    try:
        tree = ast.parse(answer.corrected_code)
    except (SyntaxError, ValueError, RecursionError):
        return result
    if not any(isinstance(n, ast.FunctionDef) and n.name == case["function"] for n in tree.body):
        return result
    result["invalid"] = 0
    result["reference_ast"] = int(ast.dump(tree) == ast.dump(ast.parse(case["corrected_code"])))
    if sandbox:
        result["passed"] = sandbox.score(answer.corrected_code, case)
    return result

def summarize(rows):
    scores = [r["scores"] for r in rows]
    summary = {k: statistics.mean(s[k] for s in scores) for k in
               ("category", "root_cause", "explanation", "invalid", "reference_ast")}
    available = all(s["passed"] is not None for s in scores)
    summary["fix_correctness"] = statistics.mean(int(s["passed"] == s["tests"]) for s in scores) if available else None
    summary["test_pass_rate"] = sum(s["passed"] for s in scores)/sum(s["tests"] for s in scores) if available else None
    summary["median_seconds"] = statistics.median(r["seconds"] for r in rows)
    return summary

def evaluate(out, adapter, skip_execution):
    import torch
    from transformers import set_seed
    from .sandbox import Sandbox
    set_seed(PROTOCOL["seed"])
    sandbox = None if skip_execution else Sandbox()
    cases = load("test")
    manifest = json.loads((ROOT / "data/manifest.json").read_text())
    if digest(ROOT / "data/test.jsonl") != manifest["test"]["sha256"]:
        raise RuntimeError("Test digest mismatch")
    engine = Engine(adapter, strict=True)
    warm = load("validation")[0]
    engine.predict(warm["buggy_code"], warm["traceback"])
    out.mkdir(parents=True, exist_ok=False)
    metadata = dict(model=MODEL, revision=REV, device=engine.device, dtype=str(engine.dtype),
        protocol=digest(ROOT/"configs/protocol.json"), test=manifest["test"]["sha256"],
        evaluator=digest(Path(__file__)), sandbox=None if skip_execution else digest(ROOT/"neuraldebugger/sandbox.py"),
        inference=digest(ROOT/"neuraldebugger/model.py"), torch=torch.__version__, mode=engine.mode)
    (out/"metadata.json").write_text(json.dumps(metadata, indent=2))
    rows = []
    with (out/"predictions.jsonl").open("x", encoding="utf-8") as f:
        for case in cases:
            begin = time.perf_counter()
            raw = engine.predict(case["buggy_code"], case["traceback"])
            seconds = time.perf_counter() - begin
            row = dict(id=case["id"], raw=raw, seconds=seconds, scores=grade(case, raw, sandbox))
            rows.append(row)
            f.write(json.dumps(row) + "\n")
            f.flush()
            print(case["id"], round(seconds, 2), row["scores"], flush=True)
    summary = summarize(rows)
    (out/"summary.json").write_text(json.dumps(summary, indent=2))
    lines = ["# Held-out case reports", ""]
    for case, row in zip(cases, rows, strict=True):
        lines += ["## " + case["id"], "", "```python", case["buggy_code"], "```", "",
                  "```text", case["traceback"], "```", "", "**Reference diagnosis** " + case["root_cause"],
                  "", "**Model output**", "", "```text", row["raw"], "```", "",
                  "```json", json.dumps(row["scores"]), "```", ""]
    (out/"cases.md").write_text("\n".join(lines), encoding="utf-8")

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--out", required=True, type=Path)
    p.add_argument("--adapter")
    p.add_argument("--skip-execution", action="store_true")
    args = p.parse_args()
    evaluate(args.out, args.adapter, args.skip_execution)

