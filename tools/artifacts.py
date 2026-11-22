"""Build a training-only payload or verify the recovered adapter on local disk."""

import argparse
import hashlib
import json
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

ROOT = Path(__file__).resolve().parents[1]
PAYLOAD = (
    "requirements.txt",
    "configs/lora.json",
    "configs/protocol.json",
    "data/train.jsonl",
    "data/validation.jsonl",
    "data/manifest.json",
    "neuraldebugger/__init__.py",
    "neuraldebugger/data.py",
    "neuraldebugger/settings.py",
    "neuraldebugger/model.py",
    "neuraldebugger/train.py",
    "THIRD_PARTY.md",
    "LICENSE",
)


def bundle(dest):
    dest.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(dest, "x", compression=ZIP_DEFLATED) as f:
        for name in PAYLOAD:
            f.write(ROOT / name, name)


def verify(folder):
    from safetensors import safe_open
    from neuraldebugger.settings import MODEL, REV

    hashes = json.loads((folder / "sha256.json").read_text())
    required = {"metadata.json", "adapter_config.json", "adapter_model.safetensors"}
    if not required.issubset(hashes):
        raise ValueError("Incomplete adapter manifest")
    for name, digest in hashes.items():
        if (
            Path(name).name != name
            or name in {".", ".."}
            or ":" in name
            or "\\" in name
        ):
            raise ValueError("Unexpected manifest path")
        if hashlib.sha256((folder / name).read_bytes()).hexdigest() != digest:
            raise ValueError("Checksum mismatch: " + name)
    meta = json.loads((folder / "metadata.json").read_text())
    if (meta["model"], meta["revision"]) != (MODEL, REV):
        raise ValueError("Incorrect base model")
    with safe_open(
        str(folder / "adapter_model.safetensors"), framework="pt", device="cpu"
    ) as tensors:
        if not tensors.keys() or not all("lora_" in key for key in tensors.keys()):
            raise ValueError("Expected LoRA tensors only")
    print("Verified adapter files and tensor index")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("action", choices=["bundle", "verify"])
    p.add_argument("path", type=Path)
    args = p.parse_args()
    (bundle if args.action == "bundle" else verify)(args.path)
