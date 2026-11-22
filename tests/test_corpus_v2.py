import itertools
import json

import pytest

from neuraldebugger.corpus import (
    DATA,
    V2,
    close,
    fingerprint,
    fixture_probes,
    observe,
    read_rows,
    sha,
)
from neuraldebugger.data import load
from neuraldebugger.sandbox import Sandbox, WASM
from neuraldebugger.trial import identity, score
from neuraldebugger.report import comparison


def test_all_split_pairs_and_frozen_hashes():
    identity()
    sets = {
        s: read_rows(s) if s != "test" else load("test")
        for s in ("test", "independent", "train", "validation")
    }
    assert len(sets["independent"]) > len(sets["test"])
    assert 150 <= sum(map(len, sets.values())) <= 300
    assert len({r["id"] for rows in sets.values() for r in rows}) == sum(
        map(len, sets.values())
    )
    shapes = {
        s: [fingerprint(r[k]) for r in rows for k in ("corrected_code", "buggy_code")]
        for s, rows in sets.items()
    }
    for a, b in itertools.combinations(sets, 2):
        assert {r["group"] for r in sets[a]}.isdisjoint({r["group"] for r in sets[b]})
        assert not any(close(x, y) for x in shapes[a] for y in shapes[b])
    assert all(
        row["source"] == "NeuralDebugger original v2" for row in sets["independent"]
    )


@pytest.mark.skipif(
    not WASM.is_file(),
    reason="Install the pinned WASI interpreter for behavioral checks",
)
def test_every_v2_reference_and_mutant():
    box = Sandbox()
    for split in ("train", "validation", "independent", "test"):
        for row in load("test") if split == "test" else read_rows(split):
            probes = fixture_probes(row)
            assert all(observe(box, row["corrected_code"], p)[0] for p in probes), row[
                "id"
            ]
            assert any(not observe(box, row["buggy_code"], p)[0] for p in probes), row[
                "id"
            ]
    row = read_rows("independent")[0]
    assert not any(score("nonsense", row, box)["passes"])


def test_paired_metrics_keep_probe_denominators():
    a = dict(
        passes=[True], seconds=1, category=True, invalid=False, cause=2, explanation=2
    )
    b = {**a, "passes": [True, False, False]}
    m = comparison([(a, a), (b, {**b, "passes": [True] * 3})], rounds=100)
    assert m["checks"]["base"] == 0.5
    assert m["repair"]["delta"] == 0.5
    assert m["explanation"]["paired_95"] == [0.0, 0.0]
