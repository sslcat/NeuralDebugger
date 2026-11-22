"""Wrap an approved SSH training-and-copy command on the controller host."""

import argparse
import json
import subprocess
import time
from pathlib import Path

from tools.artifacts import verify


def supervise(receipt_dir, adapter, command):
    receipt = json.loads((receipt_dir / "receipt.json").read_text())
    if (
        receipt.get("phase") != "training"
        or not receipt.get("id")
        or (receipt_dir / "closed").exists()
    ):
        raise RuntimeError("A bound, active training receipt is required")
    worker = None
    try:
        worker = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        previous = (-1, -1)
        for line in worker.stdout:
            # Only genuine advancing training steps extend the stall timer.
            try:
                record = json.loads(line)
                phase = record.get("phase", "main")
                progress = ({"smoke": 0, "main": 1}[phase], int(record["step"]))
                if progress > previous and "train_loss" in record:
                    (receipt_dir / "progress").touch()
                    previous = progress
            except (ValueError, TypeError, KeyError, AttributeError):
                pass
        if worker.wait() != 0:
            raise RuntimeError("Training or artifact transfer failed")
        verify(adapter)
        if json.loads((adapter / "metadata.json").read_text())["smoke"]:
            raise ValueError("Recovered only the smoke adapter")
        (receipt_dir / "recovered").touch()
    except BaseException:
        (receipt_dir / "failed").touch()
        raise
    finally:
        if worker is not None and worker.poll() is None:
            worker.kill()
            worker.wait()


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("receipt_dir", type=Path)
    p.add_argument("adapter", type=Path)
    p.add_argument("command", nargs=argparse.REMAINDER)
    args = p.parse_args()
    cmd = args.command[1:] if args.command[:1] == ["--"] else args.command
    if not cmd:
        p.error("Supply the approved SSH training and recovery command")
    supervise(args.receipt_dir, args.adapter, cmd)
