"""Resolve the pinned public base and the project's local, unmerged LoRA checkpoints."""

import hashlib
import json
from pathlib import Path

from .settings import MODEL, REV, ROOT, TRAINING


def base_directory():
    folder = ROOT / ".models/qwen"
    hashes = json.loads((ROOT / "configs/model-files.json").read_text())
    if not (folder / "model.safetensors").exists():
        from huggingface_hub import snapshot_download

        snapshot_download(MODEL, revision=REV, local_dir=folder,
                          allow_patterns=list(hashes), token=False)
    unexpected = {p.name for p in folder.iterdir()} - set(hashes) - {".cache"}
    if unexpected:
        raise ValueError("Unexpected files in the pinned base snapshot")
    for name, expected in hashes.items():
        with (folder / name).open("rb") as f:
            if hashlib.file_digest(f, "sha256").hexdigest() != expected:
                raise ValueError(f"Incorrect pinned base file: {name}")
    return str(folder)


def adapter_directory(path):
    folder = Path(path).resolve(strict=True)
    for name in ("metadata.json", "adapter_config.json", "adapter_model.safetensors"):
        file = folder / name
        if file.is_symlink() or not file.is_file() or file.resolve().parent != folder:
            raise ValueError("Expected regular local adapter files")
    if (folder / "adapter_model.bin").exists():
        raise ValueError("Only a safetensors adapter is supported")
    metadata = json.loads((folder / "metadata.json").read_text(encoding="utf8"))
    config = json.loads((folder / "adapter_config.json").read_text(encoding="utf8"))
    if (metadata["model"], metadata["revision"]) != (MODEL, REV):
        raise ValueError("Adapter metadata mismatch")
    if (config["base_model_name_or_path"], config["revision"]) != (MODEL, REV):
        raise ValueError("Adapter base mismatch")
    return folder, config


def load_adapter(model, path):
    from peft import LoraConfig, PeftModel

    folder, stored = adapter_directory(path)
    # Construct the architecture used by train.py. File-provided initialization and
    # module-loading options never reach PEFT. Compare non-default options below.
    config = LoraConfig(
        base_model_name_or_path=MODEL, revision=REV, task_type="CAUSAL_LM",
        r=TRAINING["rank"], lora_alpha=TRAINING["alpha"], lora_dropout=TRAINING["dropout"],
        target_modules=TRAINING["targets"], bias="none", inference_mode=True,
    )
    expected = config.to_dict()
    for key, value in stored.items():
        if key == "target_modules":
            value = set(value)
        if key not in expected or expected[key] != value:
            raise ValueError("Unsupported adapter configuration")
    return PeftModel.from_pretrained(model, str(folder), config=config, local_files_only=True).eval()
