import json
import pytest
from neuraldebugger.data import load
from neuraldebugger.evaluate import grade, summarize
from neuraldebugger.sandbox import Sandbox, WASM
from neuraldebugger.schema import parse


def correct(case):
    return json.dumps(
        {
            k: case[k]
            for k in ("category", "root_cause", "explanation", "corrected_code")
        }
    )


def test_parser_and_static_scores():
    case = load("train")[0]
    raw = correct(case)
    assert parse("```json\n" + raw + "\n```").category == case["category"]
    assert grade(case, raw, None)["reference_ast"] == 1
    for bad in ("[]", "{}", raw + " commentary"):
        assert grade(case, bad, None)["invalid"] == 1
    item = json.loads(raw)
    item["corrected_code"] = "def broken("
    assert grade(case, json.dumps(item), None)["invalid"] == 1


def test_aggregation_counts_failures_and_skips():
    case = load("train")[0]
    row = {"scores": grade(case, "oops", None), "seconds": 0.1}
    assert summarize([row])["fix_correctness"] is None
    row["scores"]["passed"] = 0
    assert summarize([row])["test_pass_rate"] == 0


@pytest.fixture(scope="module")
def sandbox():
    pytest.importorskip("wasmtime")
    if not WASM.exists():
        pytest.skip("WASI interpreter not installed")
    return Sandbox()


def test_sandbox_isolation(sandbox):
    assert sandbox.run("open('/etc/passwd').read()") is None
    assert sandbox.run("open('write-probe','w')") is None
    assert sandbox.run("import socket; socket.socket()") is None
    assert sandbox.run("while True: pass") is None
    assert sandbox.run("x=bytearray(256*1024*1024)") is None
    assert sandbox.run("import os; print(len(os.environ))") == b"0"


def test_sandbox_accepts_reference_and_rejects_mutant(sandbox):
    for row in load("test"):
        assert sandbox.score(row["corrected_code"], row) == len(row["checks"])
        assert sandbox.score(row["buggy_code"], row) < len(row["checks"])
