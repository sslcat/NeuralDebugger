import copy
import hashlib
import json

import pytest

from neuraldebugger.data import DATA, compile_cases, load, validate_isolation


def test_generated_files_match_reviewed_sources():
    manifest = json.loads((DATA / "manifest.json").read_text())
    splits = compile_cases()
    assert set(splits) == {"train", "validation", "test"}
    for name, rows in splits.items():
        assert load(name) == rows
        assert len(rows) == manifest[name]["rows"]
        assert (
            hashlib.sha256((DATA / f"{name}.jsonl").read_bytes()).hexdigest()
            == manifest[name]["sha256"]
        )
    assert len({r["id"] for rows in splits.values() for r in rows}) == sum(
        map(len, splits.values())
    )


def test_renaming_does_not_hide_duplicate():
    row = load("train")[0]
    duplicate = copy.deepcopy(row)
    duplicate.update(
        id="new",
        group="new",
        corrected_code=row["corrected_code"].replace("text", "argument"),
    )
    with pytest.raises(ValueError, match="near duplicate"):
        validate_isolation({"train": [row], "test": [duplicate]})
