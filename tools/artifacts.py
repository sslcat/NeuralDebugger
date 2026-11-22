"""Build a training-only payload or verify the recovered adapter on local disk."""

import argparse
import hashlib
import json
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

ROOT = Path(__file__).resolve().parents[1]
PAYLOAD = (
    "requirements.txt",
    "requirements-web.txt",
    "configs/lora.json",
    "configs/protocol.json",
    "data/train.jsonl",
    "data/validation.jsonl",
    "data/manifest.json",
    "neuraldebugger/__init__.py",
    "neuraldebugger/data.py",
    "neuraldebugger/settings.py",
    "neuraldebugger/model.py",
    "neuraldebugger/weights.py",
    "neuraldebugger/sandbox.py",
    "configs/model-files.json",
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

    folder = folder.resolve(strict=True)
    def regular_file(name):
        path = folder / name
        if path.is_symlink() or not path.is_file() or path.resolve().parent != folder:
            raise ValueError("Expected a regular file in the adapter directory")
        return path

    hashes = json.loads(regular_file("sha256.json").read_text(encoding="utf8"))
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
        with regular_file(name).open("rb") as content:
            if hashlib.file_digest(content, "sha256").hexdigest() != digest:
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
