"""Assistant-only supervised LoRA, with one optimizer update in smoke mode."""

import argparse
import hashlib
import json
import math
import random
import time
from pathlib import Path

import torch
from peft import LoraConfig, get_peft_model
from transformers import set_seed
from .data import load
from .model import Engine, messages
from .settings import MODEL, REV, ROOT, TRAINING as C


def encode(tok, row):
    conversation = messages(row["buggy_code"], row["traceback"])
    answer = json.dumps(
        {
            k: row[k]
            for k in ("category", "root_cause", "corrected_code", "explanation")
        },
        ensure_ascii=False,
    )
    prefix = tok.apply_chat_template(
        conversation, tokenize=True, add_generation_prompt=True
    )
    full = tok.apply_chat_template(
        conversation + [{"role": "assistant", "content": answer}], tokenize=True
    )
    if full[: len(prefix)] != prefix or len(full) > C["max_sequence_length"]:
        raise ValueError(f"Chat boundary or length violation: {row['id']}")
    return full, [-100] * len(prefix) + full[len(prefix) :]


def loss_for(model, example):
    x, y = example
    return model(
        input_ids=torch.tensor([x], device=model.device),
        labels=torch.tensor([y], device=model.device),
        use_cache=False,
    ).loss


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def train(out, smoke=False, expanded=False):
    if C["batch_size"] != 1 or C["optimizer"] != "AdamW":
        raise ValueError("Unsupported optimizer or microbatch")
    set_seed(C["seed"])
    rng = random.Random(C["seed"])
    engine = Engine()
    from .corpus import V2, read_rows

    directory = V2 if expanded else ROOT / "data"
    manifest = json.loads((directory / "manifest.json").read_text())
    if expanded:
        manifest = manifest["splits"]
        if engine.device != "cuda" or "4070 SUPER" not in torch.cuda.get_device_name():
            raise RuntimeError("The v2 experiment requires the local RTX 4070 SUPER")
    splits = {}
    for split in ("train", "validation"):
        if sha(directory / f"{split}.jsonl") != manifest[split]["sha256"]:
            raise ValueError(f"Changed split: {split}")
        splits[split] = [
            encode(engine.tok, r)
            for r in (read_rows(split) if expanded else load(split))
        ]
    model = get_peft_model(
        engine.model,
        LoraConfig(
            r=C["rank"],
            lora_alpha=C["alpha"],
            lora_dropout=C["dropout"],
            target_modules=C["targets"],
            task_type="CAUSAL_LM",
            bias="none",
        ),
    )
    model.peft_config["default"].base_model_name_or_path = MODEL
    model.peft_config["default"].revision = REV
    model.config.use_cache = False
    params = [p for p in model.parameters() if p.requires_grad]
    opt = torch.optim.AdamW(
        params, lr=C["learning_rate"], weight_decay=C["weight_decay"]
    )
    out.mkdir(parents=True, exist_ok=False)
    start = time.monotonic()
    if engine.device == "cuda":
        torch.cuda.reset_peak_memory_stats()
    step = 0
    best = math.inf
    metadata = dict(
        model=MODEL,
        revision=REV,
        smoke=smoke,
        device=engine.device,
        trainable=sum(p.numel() for p in params),
        config=C,
        split_hashes={k: manifest[k] for k in splits},
    )
    for epoch in range(1, (1 if smoke else C["epochs"]) + 1):
        model.train()
        order = list(splits["train"])
        rng.shuffle(order)
        if smoke:
            order = order[:1]
        for start_index in range(0, len(order), C["gradient_accumulation"]):
            batch = order[start_index : start_index + C["gradient_accumulation"]]
            opt.zero_grad(set_to_none=True)
            total = 0.0
            for example in batch:
                loss = loss_for(model, example)
                if not torch.isfinite(loss):
                    raise RuntimeError("Nonfinite training loss")
                total += loss.item()
                (loss / len(batch)).backward()
            torch.nn.utils.clip_grad_norm_(
                params, C["max_grad_norm"], error_if_nonfinite=True
            )
            opt.step()
            step += 1
            log(
                out,
                {
                    "phase": "smoke" if smoke else "main",
                    "step": step,
                    "epoch": epoch,
                    "train_loss": total / len(batch),
                },
                start,
                engine.device,
            )
        model.eval()
        val = splits["validation"][:1] if smoke else splits["validation"]
        with torch.inference_mode():
            val_loss = sum(loss_for(model, x).item() for x in val) / len(val)
        if not math.isfinite(val_loss):
            raise RuntimeError("Nonfinite validation loss")
        log(
            out,
            {"step": step, "epoch": epoch, "validation_loss": val_loss},
            start,
            engine.device,
        )
        checkpoint = out / f"epoch-{epoch}"
        model.save_pretrained(
            checkpoint, safe_serialization=True, save_embedding_layers=False
        )
        (checkpoint / "metadata.json").write_text(json.dumps(metadata, indent=2))
        if val_loss < best:
            best = val_loss
            (out / "best.txt").write_text(checkpoint.name)
        files = sorted(p for p in checkpoint.iterdir() if p.is_file())
        (checkpoint / "sha256.json").write_text(
            json.dumps({p.name: sha(p) for p in files}, indent=2)
        )
    return checkpoint


def log(out, metrics, start, device):
    metrics["elapsed_seconds"] = time.monotonic() - start
    metrics["peak_cuda_bytes"] = (
        torch.cuda.max_memory_allocated() if device == "cuda" else None
    )
    with (out / "metrics.jsonl").open("a") as f:
        f.write(json.dumps(metrics) + "\n")
    print(json.dumps(metrics), flush=True)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--smoke", action="store_true")
    p.add_argument("--expanded", action="store_true")
    args = p.parse_args()
    train(args.out, args.smoke, args.expanded)
