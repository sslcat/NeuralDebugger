# Running a hybrid locally

I expose the two hybrid modes as optional FastAPI worker backends. Start a fresh server process with the selected mode and the existing local adapter. For example, from the project directory in PowerShell:

```powershell
$env:ND_BACKEND = "hybrid-display"
$env:ND_ADAPTER = (Resolve-Path ".runs/v2-lora/epoch-3").Path
$env:HF_HUB_OFFLINE = "1"
.venv/Scripts/python -m uvicorn neuraldebugger.app:app --host 127.0.0.1 --port 18643
```

Choose `hybrid-conditioned` to pass the category as context. Choose `base` or unset `ND_BACKEND` for the default. The extra port in this example allows an existing base-only installation to keep its configuration. Each active worker owns one backbone; simultaneously analyzing in several server processes will consume additional GPU memory.

The response keeps category, root cause, explanation and corrected code in the original diagnosis object. For a hybrid, the optional `hybrid.classifier_category` is the first-stage prediction. The boolean `hybrid.conditioned` records whether the second stage saw it. If classification fails or context is too long, `hybrid.fallback` explains what happened. With an unavailable adapter, GET /api/status identifies the base model and the worker's fallback warning. Submissions stay local and the application never runs submitted code.


## Replaying the frozen comparison

I run inference replays from the project root with the pinned local foundation snapshot, epoch-3 adapter, and WASI interpreter present. This command creates a fresh directory under the ignored local experiment area. It verifies the frozen protocol, measures all four arms sequentially and writes predictions, sandbox outcomes, timings and GPU telemetry. The directory must be new.

```powershell
.venv/Scripts/python -m tools.hybrid_run --out .runs/hybrid-replay
```

I keep the original masked prose packet and its ratings alongside the measured run. A replay with different prose requires another masked review before comparing its semantic scores. [Frozen protocol](hybrid-protocol.md) · [Measured results](../results/hybrid/comparison.md)
