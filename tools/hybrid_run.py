"""Run four offline GPU evaluations sequentially with per-arm telemetry."""

import argparse
import os
from pathlib import Path
import hashlib
import json
import subprocess
import sys

from neuraldebugger import hybrid_trial
from neuraldebugger.settings import ROOT


def verified_protocol():
    release = json.loads((ROOT / "configs/release-replay.json").read_text())
    actual = hybrid_trial.protocol()
    if actual != release["protocol"]:
        raise ValueError("Release replay inputs have changed")
    for name, digest in release["support_files"].items():
        if hashlib.sha256((ROOT / name).read_bytes()).hexdigest() != digest:
            raise ValueError("Changed release input: " + name)
    return actual


def evaluate_all(directory):
    frozen = verified_protocol()
    directory.mkdir(parents=True, exist_ok=False)
    (directory / "freeze.json").write_text(json.dumps(frozen, indent=2), encoding="utf8")
    env = dict(os.environ, ND_DEVICE="cuda", HF_HUB_OFFLINE="1", PYTHONUTF8="1",
               TRANSFORMERS_VERBOSITY="error")
    executable = sys.executable
    if os.name == "nt" and sys.prefix != sys.base_prefix:
        executable = sys._base_executable
        env["__PYVENV_LAUNCHER__"] = sys.executable
    for arm in ("hybrid-conditioned", "hybrid-display", "base", "adapter"):
        with (directory / f"{arm}-gpu.csv").open("x") as log:
            monitor = subprocess.Popen(
                ["nvidia-smi", "--query-gpu=timestamp,name,utilization.gpu,memory.used,memory.total",
                 "--format=csv,nounits", "-l", "1"], stdout=log
            )
            try:
                subprocess.run(
                    [executable, "-u", "-m", "tools.hybrid_run", "--arm", arm,
                     "--out", str(directory)],
                    check=True, cwd=ROOT, env=env, timeout=1800
                )
            finally:
                monitor.terminate()
                monitor.wait(timeout=10)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=ROOT / '.runs/hybrid-replay',
                        help="Fresh destination for a replay of the frozen experiment.")
    parser.add_argument("--arm", choices=hybrid_trial.ARMS, help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.arm:
        verified_protocol()
        hybrid_trial.ADAPTER = ROOT / 'adapters'
        hybrid_trial.OUT = args.out.resolve()
        hybrid_trial.evaluate(args.arm)
    else:
        evaluate_all(args.out.resolve())
