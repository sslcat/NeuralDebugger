"""Summarize observed GPU samples and plot the actual recorded losses."""

import csv
import json
import statistics as st
from pathlib import Path
from neuraldebugger.trial import RESULT


def main():
    import matplotlib

    matplotlib.use("Agg")
    from matplotlib import pyplot as plt

    info = {}
    for stage in ("base", "train", "adapter"):
        data = list(csv.reader((RESULT / f"{stage}-gpu.csv").read_text().splitlines()))[
            1:
        ]
        samples = [
            (int(r[2]), int(r[3]))
            for r in data
            if len(r) == 5 and r[2].strip().isdigit()
        ]
        use, mem = zip(*samples)
        wall = json.loads((RESULT / f"{stage}-time.json").read_text())["wall_seconds"]
        info[stage] = dict(
            samples=len(samples),
            wall_seconds=wall,
            whole_gpu_mean_util_pct=st.mean(use),
            whole_gpu_median_util_pct=st.median(use),
            whole_gpu_max_used_mib=max(mem),
        )
    log = [
        json.loads(line) for line in (RESULT / "loss.jsonl").read_text().splitlines()
    ]
    train = [r for r in log if "train_loss" in r]
    val = [r for r in log if "validation_loss" in r]
    info["train"].update(
        steps=len(train),
        peak_torch_allocated_bytes=max(r["peak_cuda_bytes"] for r in log),
        epoch_validations=[r["validation_loss"] for r in val],
        mean_training_loss_by_epoch=[
            st.mean(r["train_loss"] for r in train if r["epoch"] == v["epoch"])
            for v in val
        ],
    )
    (RESULT / "hardware.json").write_text(json.dumps(info, indent=2))
    fig, ax = plt.subplots(figsize=(8, 4.3), layout="constrained")
    ax.plot(
        [r["step"] for r in train],
        [r["train_loss"] for r in train],
        color="#4279a3",
        alpha=0.7,
        lw=1,
        label="Training · update mean",
    )
    ax.plot(
        [r["step"] for r in val],
        [r["validation_loss"] for r in val],
        "o-",
        color="#a13e1d",
        lw=2,
        label="Validation · epoch mean",
    )
    ax.set(
        xlabel="Optimizer update",
        ylabel="Assistant-token cross-entropy",
        title="Local LoRA training on the RTX 4070 SUPER",
    )
    ax.grid(axis="y", alpha=0.2)
    ax.legend(frameon=False)
    fig.savefig(RESULT / "loss.png", dpi=160)
    plt.close(fig)
    print(json.dumps(info, indent=2))


if __name__ == "__main__":
    main()
