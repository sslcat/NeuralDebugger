import json
from contextlib import contextmanager
from types import SimpleNamespace

import pytest

from neuraldebugger import hybrid
from neuraldebugger.hybrid import Pipeline, label_from_completion, repair_messages

RAW = json.dumps(
    dict(
        category="IndexError",
        root_cause="base cause",
        explanation="base why",
        corrected_code="pass",
    )
)


class FakeEngine:
    def __init__(self, adapter=None, strict=False):
        self.mode = "adapter" if adapter else "base"
        self.warning = None
        self.device = "cpu"
        self.model = self
        self.enabled = True
        self.calls = []

    @contextmanager
    def disable_adapter(self):
        assert self.enabled
        self.enabled = False
        try:
            yield
        finally:
            self.enabled = True

    def predict(self, code, trace):
        self.calls.append((code, trace, self.enabled))
        return RAW


def make(monkeypatch, mode):
    monkeypatch.setattr(hybrid, "Engine", FakeEngine)
    p = Pipeline(mode, "fixture", strategy="training-prefix")

    def classifier(code, trace, strategy):
        assert p.engine.enabled
        return 'TypeError"', "TypeError"

    monkeypatch.setattr(p, "classify", classifier)
    return p


def test_display_changes_only_category(monkeypatch):
    p = make(monkeypatch, "hybrid-display")
    ans = p.predict("original code", "original traceback")
    assert p.engine.calls == [("original code", "original traceback", False)]
    assert ans.diagnosis().model_dump() == {**json.loads(RAW), "category": "TypeError"}
    assert not ans.conditioned and p.engine.enabled


def test_conditioning_keeps_original_fields_and_disables_adapter(monkeypatch):
    p = make(monkeypatch, "hybrid-conditioned")

    def generate(chat):
        assert not p.engine.enabled
        assert json.loads(chat[1]["content"]) == {
            "code": "full",
            "observed_failure": "trace",
            "classifier_hint": {"category": "TypeError"},
        }
        return RAW

    monkeypatch.setattr(p, "generate_chat", generate)
    assert p.predict("full", "trace").conditioned and p.engine.enabled


def test_invalid_classifier_and_overlength_hint_fallback(monkeypatch):
    p = make(monkeypatch, "hybrid-conditioned")

    def too_long(chat):
        raise OverflowError

    monkeypatch.setattr(p, "generate_chat", too_long)
    r = p.predict("full", "trace")
    assert not r.conditioned and r.diagnosis().category == "TypeError" and r.fallback
    monkeypatch.setattr(p, "classify", lambda *args: ("bad", None))
    r = p.predict("full", "trace")
    assert r.diagnosis().category == "IndexError" and r.fallback and p.engine.enabled


def test_repair_exception_restores_adapter(monkeypatch):
    p = make(monkeypatch, "hybrid-conditioned")

    def fail(chat):
        raise RuntimeError("fixture")

    monkeypatch.setattr(p, "generate_chat", fail)
    with pytest.raises(RuntimeError):
        p.predict("full", "trace")
    assert p.engine.enabled


@pytest.mark.parametrize(
    "raw,label",
    [
        ('WrongResult", "other"', "WrongResult"),
        ('KeyError"}', "KeyError"),
        ('bad hint"', None),
        ("IndexError", None),
        ('TypeError; ignore instructions"', None),
    ],
)
def test_strict_category_completion(raw, label):
    assert label_from_completion(raw) == label


def test_missing_adapter_uses_base(monkeypatch):
    monkeypatch.setattr(hybrid, "Engine", FakeEngine)
    p = Pipeline("hybrid-conditioned", None)
    assert (
        p.mode == "base"
        and p.warning
        and p.predict("a", "b").diagnosis().category == "IndexError"
    )
