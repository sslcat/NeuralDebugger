# NeuralDebugger

I built NeuralDebugger to test whether a small open-weight coding model can diagnose a Python failure, explain what went wrong, and produce a correction that passes behavioral checks. The workbench runs on a local FastAPI server. The same model loader and prompt power the benchmark.

**Current result.** The original Qwen model fixed 10 of 12 held-out functions and passed 32 of 36 executable checks. It sometimes produced a working patch alongside a false explanation. I completed separate one-update LoRA smoke runs on CPU and GPU and verified both saved adapters. The main Runpod experiment is at the paid preflight gate. The workbench defaults to the original model. [All case reports](results/base-v1/cases.md) · [Qualitative review](results/base-v1/review.md) · [Paid preflight](docs/preflight.md)

![The local workbench showing the model's actual response to a clock conversion failure](docs/workbench.png)

The screenshot is an unedited base-model response. Its proposed `divmod` repair works, but its explanation of Python 3's built-in `divmod` is inaccurate. I evaluate the diagnostic prose separately from the program.

## Run the workbench

I used Python 3.12.15. From this checkout, install the pinned dependencies into an isolated environment. For CPU-only operation, install the CPU wheel for PyTorch first. For CUDA, choose the wheel matching the installed driver. My exact Windows package inventory is included. [Windows environment](configs/windows-environment.txt)

```powershell
uv venv --python 3.12 .venv
uv pip install --python .venv/Scripts/python.exe torch==2.8.0 --index-url https://download.pytorch.org/whl/cu128
uv pip install --python .venv/Scripts/python.exe -r requirements-benchmark.txt
.venv/Scripts/python -m uvicorn neuraldebugger.app:app --host 127.0.0.1 --port 18642
```

On Linux or macOS, use `.venv/bin/python`. Open [the local workbench](http://127.0.0.1:18642). The first analysis loads the public pinned model, approximately 3.1 GB of weights. This checkout can also use the downloaded snapshot under `.models/qwen`. I run it offline once the snapshot is present. No paid inference API is required.

Paste a Python function and its exception or failing input/output pair. Select **Analyze code**, then inspect the diagnosis and copy the proposed correction. The application never executes a submission. It identifies the actually loaded model after the first request. An invalid model response gets an error state.

| Setting | Behavior |
|---|---|
| `ND_DEVICE=auto` | Uses CUDA when available with more than 4.5 GiB free, otherwise CPU. Also accepts cpu or cuda. |
| `ND_BACKEND=base` | Default pinned Transformers backend. |
| `ND_BACKEND=adapter`, `ND_ADAPTER=PATH` | Loads a PEFT checkpoint with matching NeuralDebugger metadata. Reports fallback if unavailable. |
| `ND_TIMEOUT=150` | Seconds before the service terminates its inference worker. Includes first load. |
| `ND_CPU_THREADS=6` | CPU intra-op thread count used for the recorded baseline. |
| `HF_HUB_OFFLINE=1` | Uses already-present artifacts without contacting Hugging Face. |

The API exposes `GET /api/status` and `POST /api/analyze`. For example, send `{"code":"def double(x):\n    return x + '2'","traceback":"double(3) raised TypeError: unsupported operand type(s) for +: 'int' and 'str'. Expected 6."}`. The response includes category, root cause, corrected program, explanation, active mode and device.

## What I measured

I evaluated the original model before updating any adapter. I used a family-disjoint 23/4/12 split and kept the held-out file out of the training payload. The 39 functions contain 36 original cases and three attributed MBPP adaptations. The benchmark executes patches in isolated WebAssembly instances; it includes invalid and incorrect responses in its denominators.

| Base-model measure | Result |
|---|---:|
| All behavioral checks passed | 10/12 (83.3%) |
| Individual checks passed | 32/36 (88.9%) |
| Exact error category | 7/12 (58.3%) |
| Root-cause lexical proxy | 7/12 (58.3%) |
| Automatic explanation rubric | 1.58/2 |
| Invalid/unusable responses | 0/12 |
| Reference AST match | 5/12 |
| Median warmed CPU inference | 21.69 s |

I used a Ryzen 7 9800X3D for full-model inference and the local LoRA smoke because other applications were occupying most of the 4070 SUPER's VRAM. When GPU headroom became available, I also ran the full-model smoke on the RTX 4070 SUPER. It reached 3.77 GiB peak PyTorch allocation, with training loss 1.2568 and a one-example validation loss of 1.6283. The update plus validation took 0.86 seconds after loading. The CPU smoke trained 1,089,536 adapter parameters for one step, with a training loss of 1.2468 and one validation-example loss of 1.6242. These measurements establish that the training and checkpoint paths work. A main-run learning curve and a base-versus-trained result require the approved experiment. [CPU smoke log](results/local-smoke/metrics.jsonl) · [GPU smoke log](results/cuda-smoke/metrics.jsonl) · [Model card](MODEL_CARD.md)

## Reproduce the checks

```bash
python tools/fetch_sandbox.py
python -m neuraldebugger.data
python -m pytest -q
python -m neuraldebugger.evaluate --out results/base-reproduction
```

I used AI coding assistance from OpenAI Codex to implement the application, write and check fixtures, run experiments, draft documentation and review model responses. The behavioral scores come from actual executions. Qualitative judgments are labeled as AI-assisted.

## Engineering notes

- [Architecture and request lifecycle](docs/architecture.md)
- [Dataset construction, split rules and attribution](data/README.md)
- [Training configuration and artifact recovery](docs/training.md)
- [Benchmark protocol, metrics and comparison](docs/evaluation.md)
- [Transformer, optimizer, LoRA and evaluation mathematics](docs/math.md)
- [Runpod costs, shutdown controller and approval status](docs/preflight.md)
- [Third-party notices](THIRD_PARTY.md) and [original code license](LICENSE)

## Let's Connect

I'm happy to discuss the implementation, training methodology, experiments and results. [Find me on GitHub](https://github.com/sslcat)
