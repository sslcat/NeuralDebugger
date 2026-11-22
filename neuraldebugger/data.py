"""Compile reviewed, repository-owned fixtures. Never pass submission text here."""

import ast
import hashlib
import json
import re
from collections import defaultdict
from difflib import SequenceMatcher

from .settings import ROOT
from .sandbox import Sandbox

DATA = ROOT / "data"


def canon(code):
    return ast.dump(ast.parse(code), include_attributes=False)


def shape(code):
    tree = ast.parse(code)
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.Name, ast.arg)):
            attr = (
                "name"
                if isinstance(node, ast.FunctionDef)
                else "id"
                if isinstance(node, ast.Name)
                else "arg"
            )
            setattr(node, attr, "_")
    return canon(ast.unparse(tree))


def validate_isolation(splits):
    seen = []
    for split, rows in splits.items():
        for row in rows:
            for other_split, old, signature in seen:
                if other_split == split:
                    continue
                if row["group"] == old["group"]:
                    raise ValueError(f"shared group: {row['group']}")
                current = shape(row["corrected_code"])
                if (
                    SequenceMatcher(None, signature, current, autojunk=False).ratio()
                    >= 0.965
                ):
                    raise ValueError(f"near duplicate: {old['id']}, {row['id']}")
            seen.append((split, row, shape(row["corrected_code"])))


def observe(box, code, name, checks):
    failures = []
    for args, expected in checks:
        call = f"{name}({', '.join(map(repr, args))})"
        # Return repr as a string, including for non-literal objects in legacy fixtures.
        script = (code + "\ntry:\n print(repr(('value', repr(" + call + "))))"
                  + "\nexcept Exception as exc:\n print(repr((type(exc).__name__, str(exc))))")
        raw = box.run(script)
        if raw is None:
            raise ValueError("Legacy fixture failed inside WASI")
        kind, value = ast.literal_eval(raw.decode("utf8"))
        if kind != "value":
            failures.append((kind, f"{call}\n{kind}: {value}"))
            continue
        try:
            if ast.literal_eval(value) == expected:
                continue
        except (ValueError, SyntaxError):
            # One reviewed mutation returns a bound method rather than a literal.
            pass
        display = re.sub(r" at 0x[0-9A-Fa-f]+", "", value)
        failures.append(("WrongResult", f"{call}\nAssertionError: expected {expected!r}, observed {display}"))
    return failures


def compile_cases():
    box = Sandbox()
    splits = defaultdict(list)
    for s in json.loads((DATA / "sources.json").read_text()):
        ref = s["reference"]
        if ref.count(s["old"]) != 1:
            raise ValueError(f"ambiguous mutation {s['id']}")
        mutant = ref.replace(s["old"], s["bad"])
        if observe(box, ref, s["function"], s["checks"]):
            raise ValueError(f"incorrect reference {s['id']}")
        failures = observe(box, mutant, s["function"], s["checks"])
        if not failures:
            raise ValueError(f"undetected mutation {s['id']}")
        category, trace = failures[0]
        row = dict(
            id=s["id"],
            group=s["id"],
            buggy_code=mutant,
            traceback=trace,
            root_cause=s["cause"],
            corrected_code=ref,
            explanation=s["ex"],
            category=category,
            source=s["source"],
            anchors=s["anchors"],
            function=s["function"],
            checks=s["checks"],
        )
        splits[s["split"]].append(row)
    validate_isolation(splits)
    return splits


def load(split):
    return [
        json.loads(line) for line in (DATA / f"{split}.jsonl").read_text().splitlines()
    ]


def main():
    manifest = {}
    for name, rows in compile_cases().items():
        payload = "".join(
            json.dumps(row, ensure_ascii=True) + "\n" for row in rows
        ).encode()
        (DATA / f"{name}.jsonl").write_bytes(payload)
        manifest[name] = {
            "rows": len(rows),
            "sha256": hashlib.sha256(payload).hexdigest(),
        }
    (DATA / "manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    print(manifest)


if __name__ == "__main__":
    main()
