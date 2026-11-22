import hashlib
import json
from pathlib import Path

import pytest

from neuraldebugger import weights
from neuraldebugger.schema import Request
from neuraldebugger.settings import ROOT
from tools.hybrid_run import verified_protocol


def test_packaged_adapter_and_release_protocol():
    path, config = weights.adapter_directory(ROOT / "adapters/epoch-3")
    manifest = json.loads((path / "sha256.json").read_text())
    benchmark = json.loads((ROOT / "results/v2/checkpoints.json").read_text())
    assert manifest["adapter_model.safetensors"] == benchmark["sha256"]
    for name, expected in manifest.items():
        assert hashlib.sha256((path / name).read_bytes()).hexdigest() == expected
    assert config["peft_type"] == "LORA"
    verified_protocol()


def test_adapter_requires_safe_local_files(tmp_path):
    for name in ("metadata.json", "adapter_config.json", "adapter_model.bin"):
        (tmp_path / name).write_text("{}")
    with pytest.raises(ValueError, match="regular local adapter files"):
        weights.adapter_directory(tmp_path)
    (tmp_path / "adapter_model.safetensors").touch()
    with pytest.raises(ValueError, match="Only a safetensors"):
        weights.adapter_directory(tmp_path)


def test_request_cannot_select_weights():
    with pytest.raises(ValueError):
        Request.model_validate({"code": "pass", "traceback": "example", "adapter": "example"})


def test_snapshot_identity_and_unexpected_files(tmp_path, monkeypatch):
    monkeypatch.setattr(weights, "ROOT", tmp_path)
    folder = tmp_path / ".models/qwen"
    folder.mkdir(parents=True)
    name = "model.safetensors"
    (folder / name).write_bytes(b"test fixture")
    (tmp_path / "configs").mkdir()
    manifest = {name: hashlib.sha256(b"test fixture").hexdigest()}
    (tmp_path / "configs/model-files.json").write_text(json.dumps(manifest))
    assert Path(weights.base_directory()) == folder
    (folder / name).write_bytes(b"changed fixture")
    with pytest.raises(ValueError, match="Incorrect pinned"):
        weights.base_directory()
    (folder / "unexpected.json").touch()
    with pytest.raises(ValueError, match="Unexpected files"):
        weights.base_directory()
