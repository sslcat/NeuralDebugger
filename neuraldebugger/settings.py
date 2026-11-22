import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODEL = "Qwen/Qwen2.5-Coder-1.5B-Instruct"
REV = "2e1fd397ee46e1388853d2af2c993145b0f1098a"
PROTOCOL = json.loads((ROOT / "configs/protocol.json").read_text())
TRAINING = json.loads((ROOT / "configs/lora.json").read_text())
