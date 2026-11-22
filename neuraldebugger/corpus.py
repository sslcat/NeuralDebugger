"""Build the v2 corpus using only the WASI guest for candidate program execution."""

import argparse
import ast
import builtins
import copy
import hashlib
import json
import random
from collections import Counter, defaultdict
from difflib import SequenceMatcher
from pathlib import Path

from .data import DATA, load
from .sandbox import Sandbox
from .settings import ROOT

V2 = DATA / "v2"
LEGACY = "0933538b9be3df1368de629dd5b1a960c867f33388563ac35ece5f4a97ae3627"
MBPP = "ca95deaa9a01ef0a6f439f88bcf0dd3db3563d22f22aad6cae04ebb9a8d8c8e9"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_rows(name):
    return [
        json.loads(line)
        for line in (V2 / f"{name}.jsonl").read_text(encoding="utf8").splitlines()
    ]


def fixture_probes(row):
    if "probes" in row:
        return row["probes"]
    return [
        dict(expr=f"{row['function']}({', '.join(map(repr, args))})", want=repr(want))
        for args, want in row["checks"]
    ]


def observe(box, code, probe):
    expr = probe["expr"]
    script = (
        code
        + "\ntry:\n    print(repr(('value', "
        + expr
        + ")))\nexcept Exception as exc:\n    print(repr(('exception',type(exc).__name__,str(exc))))"
    )
    raw = box.run(script)
    try:
        result = ast.literal_eval(raw.decode()) if raw else None
    except (ValueError, SyntaxError, UnicodeError, RecursionError):
        result = None
    if not isinstance(result, tuple) or len(result) not in (2, 3):
        return False, "Unusable", "guest failed or returned unusable output"
    if result[0] == "exception" and len(result) == 3:
        return False, result[1], f"{expr}\n{result[1]}: {result[2]}"
    if result[0] != "value" or len(result) != 2:
        return False, "Unusable", "unrecognized guest output"
    want = ast.literal_eval(probe["want"])
    actual = result[1]
    return (
        isinstance(want, bool) == isinstance(actual, bool) and actual == want,
        "WrongResult",
        f"{expr}\nAssertionError: expected {want!r}, observed {actual!r}",
    )


def fingerprint(code):
    tree = ast.parse(code)
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            node.name = "FUNCTION"
            if ast.get_docstring(node) is not None:
                node.body.pop(0)
        elif isinstance(node, ast.Name) and node.id not in vars(builtins):
            node.id = "VAR"
        elif isinstance(node, ast.arg):
            node.arg = "VAR"
        elif isinstance(node, ast.Constant):
            node.value = type(node.value).__name__
    return tuple(
        ast.dump(n)
        if isinstance(n, (ast.Name, ast.Constant))
        else ("attr:" + n.attr if isinstance(n, ast.Attribute) else type(n).__name__)
        for n in ast.walk(tree)
    )


def close(a, b):
    if min(len(a), len(b)) * 2 < 0.91 * (len(a) + len(b)):
        return False
    m = SequenceMatcher(None, a, b, autojunk=False)
    return m.quick_ratio() >= 0.91 and m.ratio() >= 0.91


def verified(box, meta, ref, bug, probes):
    if not all(observe(box, ref, p)[0] for p in probes):
        return None
    failures = [v for p in probes if not (v := observe(box, bug, p))[0]]
    if not failures or failures[0][1] == "Unusable":
        return None
    # Reject unsupported library failures or timeouts even if another probe succeeds.
    if any(
        f[1] in {"ImportError", "ModuleNotFoundError", "Unusable"} for f in failures
    ):
        return None
    _, cat, trace = failures[0]
    if meta.get("contract"):
        trace = meta["contract"] + "\n" + trace
    return {
        **meta,
        "buggy_code": bug,
        "corrected_code": ref,
        "probes": probes,
        "category": cat,
        "traceback": trace,
    }


# Each transformation names the changed operation; mutation text is specific to the selected expression.
RULES = {
    ast.Add: (ast.Sub, "subtracts the right operand instead of adding it", "addition"),
    ast.Sub: (
        ast.Add,
        "adds the right operand instead of taking the difference",
        "subtraction",
    ),
    ast.Mult: (
        ast.Add,
        "adds operands where their product is required",
        "multiplication",
    ),
    ast.Mod: (
        ast.FloorDiv,
        "computes the quotient where the remainder is needed",
        "remainder",
    ),
    ast.FloorDiv: (
        ast.Mod,
        "keeps the remainder where the integral quotient is needed",
        "floor division",
    ),
    ast.Pow: (
        ast.BitXor,
        "performs bitwise XOR in place of exponentiation",
        "exponentiation",
    ),
    ast.BitAnd: (
        ast.BitOr,
        "includes either operand's set bits or members where intersection is required",
        "intersection",
    ),
    ast.And: (
        ast.Or,
        "accepts either condition although both must hold",
        "conjunction",
    ),
    ast.Or: (
        ast.And,
        "requires both conditions although either is sufficient",
        "disjunction",
    ),
    ast.Eq: (
        ast.NotEq,
        "accepts unequal values where equality is required",
        "equality",
    ),
    ast.NotEq: (
        ast.Eq,
        "accepts equal values where inequality is required",
        "inequality",
    ),
    ast.Lt: (
        ast.LtE,
        "includes equality at an exclusive upper boundary",
        "strict comparison",
    ),
    ast.LtE: (
        ast.Lt,
        "excludes equality at an inclusive upper boundary",
        "inclusive comparison",
    ),
    ast.Gt: (
        ast.GtE,
        "includes equality at an exclusive lower boundary",
        "strict comparison",
    ),
    ast.GtE: (
        ast.Gt,
        "excludes equality at an inclusive lower boundary",
        "inclusive comparison",
    ),
    ast.In: (
        ast.NotIn,
        "takes the branch for absent rather than present members",
        "membership",
    ),
}


def mutations(code):
    tree = ast.parse(code)
    for i, node in enumerate(ast.walk(tree)):
        choices = []
        if isinstance(node, (ast.BinOp, ast.BoolOp)) and type(node.op) in RULES:
            choices = [("op", RULES[type(node.op)])]
        if (
            isinstance(node, ast.Compare)
            and len(node.ops) == 1
            and type(node.ops[0]) in RULES
        ):
            choices = [("ops", RULES[type(node.ops[0])])]
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            swaps = {
                "min": ("max", "largest", "smallest"),
                "max": ("min", "smallest", "largest"),
                "all": ("any", "one condition", "every condition"),
                "any": ("all", "every condition", "at least one condition"),
            }
            if node.func.id in swaps:
                new, wrong, right = swaps[node.func.id]
                choices = [
                    (
                        "func",
                        (
                            new,
                            f"selects {wrong} where the contract requires {right}",
                            node.func.id,
                        ),
                    )
                ]
            if node.func.id == "range" and len(node.args) in (1, 2):
                choices = [
                    (
                        "args",
                        (
                            None,
                            "omits the final iteration by reducing the exclusive stop",
                            "original range stop",
                        ),
                    )
                ]
        for attr, (new, reason, operation) in choices:
            t = copy.deepcopy(tree)
            n = list(ast.walk(t))[i]
            orig = ast.unparse(n)
            if attr == "ops":
                n.ops = [new()]
            elif attr == "func":
                n.func = ast.Name(id=new, ctx=ast.Load())
            elif attr == "args":
                n.args[-1] = ast.BinOp(
                    left=n.args[-1], op=ast.Sub(), right=ast.Constant(value=1)
                )
            else:
                n.op = new()
            expr = ast.unparse(n)
            yield (
                operation,
                ast.unparse(t),
                f"The expression {expr!r} {reason}.",
                f"Use {orig!r} at that operation to restore the intended {operation}.",
            )


def public_cases(path, box, splits, seen, stats):
    if sha(path) != MBPP:
        raise ValueError("Unexpected MBPP revision")
    tasks = json.loads(path.read_text(encoding="utf8"))
    random.Random(7341).shuffle(tasks)
    rules = Counter()
    chosen = 0
    for s in tasks:
        if chosen >= 110:
            break
        task = s["task_id"]
        if task in {8, 12, 14} or s["test_imports"] or len(s["code"]) > 1000:
            continue
        probes = []
        for source in s["test_list"]:
            node = ast.parse(source).body[0]
            if not isinstance(node, ast.Assert) or not isinstance(
                node.test, ast.Compare
            ):
                break
            check = node.test
            if len(check.ops) != 1 or not isinstance(check.ops[0], ast.Eq):
                break
            try:
                ast.literal_eval(check.comparators[0])
            except (ValueError, SyntaxError):
                break
            probes.append(
                dict(
                    expr=ast.unparse(check.left), want=ast.unparse(check.comparators[0])
                )
            )
        if len({p["expr"] for p in probes}) < 3:
            continue
        ref = ast.unparse(ast.parse(s["code"]))
        name = next(
            (n.name for n in ast.parse(ref).body if isinstance(n, ast.FunctionDef)),
            None,
        )
        if not name:
            continue
        fp = fingerprint(ref)
        if any(close(fp, f) for f in seen):
            stats["public_near_duplicate_exclusions"] += 1
            continue
        if not all(observe(box, ref, p)[0] for p in probes):
            continue
        options = sorted(mutations(ref), key=lambda v: rules[v[0]])
        for kind, bug, cause, ex in options[:8]:
            if rules[kind] >= 15:
                continue
            split = "validation" if chosen % 9 == 0 else "train"
            meta = dict(
                id=f"mbpp-{task}",
                group=f"mbpp-{task}",
                function=name,
                source=f"MBPP sanitized #{task}",
                topic=kind,
                contract=s["prompt"],
                root_cause=cause,
                explanation=ex,
            )
            row = verified(box, meta, ref, bug, probes)
            if row:
                splits[split].append(row)
                seen.append(fp)
                rules[kind] += 1
                chosen += 1
                break
    stats["public_transformations"] = dict(rules)


def build(path):
    if sha(DATA / "test.jsonl") != LEGACY:
        raise RuntimeError("Legacy holdout changed")
    box = Sandbox()
    splits = {s: load(s) for s in ("test", "train", "validation")}
    splits["independent"] = []
    stats = Counter()
    seen = []
    for split, rows in splits.items():
        for row in rows:
            for p in fixture_probes(row):
                assert observe(box, row["corrected_code"], p)[0], row["id"]
            assert any(
                not observe(box, row["buggy_code"], p)[0] for p in fixture_probes(row)
            ), row["id"]
            seen.append(fingerprint(row["corrected_code"]))
    for file in ["independent-sources.json", "train-sources.json"]:
        for s in json.loads((V2 / file).read_text(encoding="utf8")):
            ref = s["reference"]
            assert ref.count(s["old"]) == 1, s["id"]
            meta = {
                k: s[k]
                for k in (
                    "id",
                    "group",
                    "function",
                    "source",
                    "root_cause",
                    "explanation",
                    "topic",
                )
            }
            row = verified(box, meta, ref, ref.replace(s["old"], s["bad"]), s["probes"])
            assert row, s["id"]
            splits[s["split"]].append(row)
            seen.append(fingerprint(ref))
    public_cases(path, box, splits, seen, stats)
    # Manual family review of upstream task IDs before inference.
    families = {
        "max-product": [120, 415, 468, 463],
        "rotations": [9, 802],
        "power-of-two": [6, 167, 138],
        "power-sum": [267, 271, 420],
        "parity-filter": [437, 426],
        "subarray": [69, 576, 282],
        "factor-related": [96, 295],
        "character-count": [242, 172],
        "sequence-sum": [728, 65, 796],
        "sorting-algorithms": [141, 428],
    }
    family_for = {f"mbpp-{i}": name for name, ids in families.items() for i in ids}
    validation_families = {
        family_for[r["id"]] for r in splits["validation"] if r["id"] in family_for
    }
    development = splits["validation"] + splits["train"]
    val_ids = {r["id"] for r in splits["validation"]}
    splits["train"], splits["validation"] = [], []
    from transformers import AutoTokenizer
    from .model import location
    from .train import encode

    tok = AutoTokenizer.from_pretrained(location())
    audit = []
    for row in development:
        if row["id"] == "mbpp-591":
            audit.append([row["id"], "held-out swap family"])
            continue
        if row["id"] in family_for:
            row["group"] = family_for[row["id"]]
        try:
            encode(tok, row)
        except ValueError:
            audit.append([row["id"], "token budget"])
            continue
        dest = (
            "validation"
            if row["id"] in val_ids or row["group"] in validation_families
            else "train"
        )
        splits[dest].append(row)
    # Exclude development rows structurally too close to a held-out fixture, including buggy ASTs.
    held = [
        (r["id"], fingerprint(r[key]))
        for s in ("test", "independent")
        for r in splits[s]
        for key in ("corrected_code", "buggy_code")
    ]
    accepted = list(held)
    exclusions = []
    for split in ("validation", "train"):
        kept = []
        for r in splits[split]:
            shapes = [fingerprint(r[k]) for k in ("corrected_code", "buggy_code")]
            dup = next(
                (
                    rid
                    for rid, other in accepted
                    if any(close(f, other) for f in shapes)
                ),
                None,
            )
            if dup:
                exclusions.append([r["id"], dup])
                continue
            kept.append(r)
        splits[split] = kept
        accepted.extend(
            (r["id"], fingerprint(r[k]))
            for r in kept
            for k in ("corrected_code", "buggy_code")
        )
    manifest = {}
    for split, rows in splits.items():
        # The legacy benchmark is always read from its immutable original location.
        out = DATA / "test.jsonl" if split == "test" else V2 / f"{split}.jsonl"
        if split != "test":
            out.write_bytes("".join(json.dumps(r) + "\n" for r in rows).encode())
        manifest[split] = dict(rows=len(rows), sha256=sha(out))
    info = dict(splits=manifest, exclusions=exclusions + audit, selection=dict(stats))
    (V2 / "manifest.json").write_bytes((json.dumps(info, indent=2) + "\n").encode())
    print(json.dumps(info, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("mbpp", type=Path)
    build(parser.parse_args().mbpp)
