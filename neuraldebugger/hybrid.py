"""A short adapter decode followed by an unmerged, adapter-disabled repair."""

import builtins
import json
import re
from dataclasses import dataclass
from pathlib import Path

from .model import Engine, messages
from .schema import parse
from .settings import PROTOCOL, ROOT

CONFIG = json.loads((ROOT / "configs/hybrid.json").read_text())
HYBRIDS = ("hybrid-display", "hybrid-conditioned")


def label_from_completion(raw):
    match = re.match(r'^([A-Za-z][A-Za-z0-9_]{0,79})"', raw)
    if not match:
        return None
    label = match.group(1)
    cls = getattr(builtins, label, None)
    if (
        label == "WrongResult"
        or (isinstance(cls, type) and issubclass(cls, BaseException))
        or label.endswith(("Error", "Exception"))
    ):
        return label
    return None


def repair_messages(code, traceback, category):
    chat = messages(code, traceback)
    chat[0]["content"] += CONFIG["repair_instruction"]
    payload = json.loads(chat[1]["content"])
    payload["classifier_hint"] = {"category": category}
    chat[1]["content"] = json.dumps(payload, ensure_ascii=False)
    return chat


@dataclass
class Prediction:
    repair_raw: str
    classifier_raw: str | None = None
    classifier_label: str | None = None
    conditioned: bool = False
    fallback: str | None = None

    def diagnosis(self):
        answer = parse(self.repair_raw)
        if self.classifier_label:
            answer = answer.model_copy(update={"category": self.classifier_label})
        return answer


class Pipeline:
    def __init__(self, backend="base", adapter=None, *, strict=False, strategy=None):
        if backend not in ("base", "adapter", *HYBRIDS):
            raise ValueError("Unknown inference backend")
        if strict and backend != "base" and not adapter:
            raise ValueError("Expected an adapter path")
        self.engine = Engine(adapter if backend != "base" else None, strict=strict)
        self.mode = backend if self.engine.mode == "adapter" else "base"
        self.warning = self.engine.warning
        if backend != "base" and not adapter:
            self.warning = "Adapter path missing. The base model is active."
        self.strategy = strategy
        if self.mode in HYBRIDS and strategy is None:
            self.strategy = json.loads(
                (ROOT / "configs/hybrid-selection.json").read_text()
            )["strategy"]

    def generate_chat(self, chat, *, prefix="", short=False):
        import torch

        e = self.engine
        prompt = (
            e.tok.apply_chat_template(chat, tokenize=False, add_generation_prompt=True)
            + prefix
        )
        tokens = e.tok(prompt, add_special_tokens=False, return_tensors="pt")
        size = tokens.input_ids.shape[1]
        if size > PROTOCOL["max_input_tokens"]:
            raise OverflowError("Input exceeds the 1536-token context budget.")
        args = {"stop_strings": ['"'], "tokenizer": e.tok} if short else {}
        with torch.inference_mode():
            out = e.model.generate(
                **tokens.to(e.device),
                do_sample=False,
                num_beams=1,
                max_new_tokens=CONFIG["category_tokens"]
                if short
                else PROTOCOL["max_new_tokens"],
                pad_token_id=e.tok.eos_token_id,
                **args,
            )
        return e.tok.decode(out[0, size:], skip_special_tokens=True)

    def classify(self, code, traceback, strategy):
        chat = messages(code, traceback)
        if strategy == "category-only":
            chat[0]["content"] = CONFIG["category_system"]
        elif strategy != "training-prefix":
            raise ValueError("Unknown classification prompt")
        raw = self.generate_chat(chat, prefix=CONFIG["prefix"], short=True)
        return raw, label_from_completion(raw)

    def predict(self, code, traceback):
        if self.mode not in HYBRIDS:
            return Prediction(self.engine.predict(code, traceback))
        fallback = None
        try:
            raw, label = self.classify(code, traceback, self.strategy)
        except OverflowError:
            raw, label = None, None
        conditioned = label is not None and self.mode == "hybrid-conditioned"
        if label is None:
            fallback = "Classifier unavailable for this input; using the base category and repair."
        # The API worker serializes requests. PEFT restores adapter state on exit, even on exceptions.
        with self.engine.model.disable_adapter():
            if conditioned:
                try:
                    repair = self.generate_chat(repair_messages(code, traceback, label))
                except OverflowError:
                    conditioned = False
                    fallback = "Hint exceeded the input budget; used the full original request for base repair."
            if not conditioned:
                repair = self.engine.predict(code, traceback)
        return Prediction(repair, raw, label, conditioned, fallback)
