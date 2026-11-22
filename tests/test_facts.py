import json
from neuraldebugger.data import load
from neuraldebugger.facts import checked_prose
from neuraldebugger.schema import parse
from neuraldebugger.settings import ROOT


def test_actual_empty_string_truthiness_regression():
    case = next(r for r in load("test") if r["id"] == "predicate-call")
    prediction = next(
        r
        for r in map(
            json.loads,
            (ROOT / "results/base-v1/predictions.jsonl").read_text().splitlines(),
        )
        if r["id"] == case["id"]
    )
    answer = parse(prediction["raw"])
    assert bool("   ".strip) and not bool("   ".strip()) and bool(" x ".strip())
    checked, source = checked_prose(case["buggy_code"], case["traceback"], answer)
    assert source == "Python semantics check"
    assert (
        "bound method" in checked.root_cause
        and "empty result is false" in checked.explanation
    )
    assert checked.corrected_code == answer.corrected_code
    assert checked_prose(case["corrected_code"], case["traceback"], answer) == (
        answer,
        None,
    )
    assert checked_prose(case["buggy_code"], "nonblank(custom_object)", answer) == (
        answer,
        None,
    )
