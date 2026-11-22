import json
import pytest
from neuraldebugger.compare import compare
from neuraldebugger.data import load


def make(folder, mode, *, incomplete=False):
    folder.mkdir()
    config = dict.fromkeys(
        (
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
        ),
        "same",
    )
    (folder / "metadata.json").write_text(json.dumps({**config, "mode": mode}))
    scores = dict(
        category=1,
        root_cause=1,
        explanation=2,
        invalid=0,
        reference_ast=1,
        tests=3,
        passed=3,
    )
    rows = [dict(id=r["id"], seconds=1, scores=scores) for r in load("test")]
    (folder / "predictions.jsonl").write_text(
        "\n".join(map(json.dumps, rows[:-1] if incomplete else rows))
    )


def test_paired_comparison_identical_scores(tmp_path):
    base, adapter = tmp_path / "base", tmp_path / "adapter"
    make(base, "base")
    make(adapter, "adapter")
    result = compare(base, adapter)
    assert len(result["all_pairs"]) == 12
    assert result["metrics"]["fix_correctness"]["paired_95"] == [0, 0]
    assert result["metrics"]["invalid"]["relative"] is None


def test_incomplete_run_cannot_be_compared(tmp_path):
    base, adapter = tmp_path / "base", tmp_path / "adapter"
    make(base, "base")
    make(adapter, "adapter", incomplete=True)
    with pytest.raises(ValueError, match="Incomplete"):
        compare(base, adapter)
