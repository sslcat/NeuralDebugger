# Local release audit

On 22 November 2026 I started with commit `046c126b7223` and used a separate local clone, clean Python environments, and an anonymous download of the exact model revision. All compute ran on this workstation. The audit required internet access for public packages and initial artifact downloads. I used offline inference, training and evaluation after fetching the artifacts.

## Installation and reproduction

| Check | Evidence |
|---|---|
| CPU installation | Windows, Python 3.12.15, PyTorch 2.8.0+cpu. PyTorch reported no CUDA support. The FastAPI worker returned a real clock-conversion diagnosis and reported CPU. |
| CUDA installation | Separate Windows environment, PyTorch 2.8.0+cu128 and an RTX 4070 SUPER. Both installations used the same release manifests. |
| Model fetch | I downloaded the public 1.5B snapshot into the clone, including the tokenizer. The release checks all eight files against SHA-256 digests. The WASI interpreter passed its independent pinned hash. |
| Training | I ran the full 90-update, three-epoch schedule in a supervised process with a 900-second cutoff. It took 70.81 seconds including process startup and saving. Peak tensor allocation was 5.10 GiB. Validation losses were 0.68168, 0.39454 and 0.29034. |
| Selected adapter | Epoch 3 was again the best. The rerun produced `abdd2891cda732bf625990d754a4b7cbdda50d155a60d51fae79474ead48db68`. The measured adapter included in the source release has digest `96ac4f90bbf04f6c9e0d9ab67a99cac5fcb5d575f854866fc7c3ea57ff9ce92e`. I use the latter for the published comparisons. |

I preserve the original predictions, semantic reviews, loss traces, and resource measurements. The release replay records a separate input manifest for the hardened loader. Inference uses the original greedy prompts, checkpoint, tokenizer and 24 independent plus 12 legacy functions. The project targets one user on loopback. [All four configurations](../results/hybrid/comparison.md) · [Reproduction commands](hybrid-usage.md)

I regenerated all 144 held-out diagnoses with the measured adapter and compared the original raw outputs, routes, invalid flags, categories and individual probe outcomes. Every row matched. Display-only returned the exact base repair text on all 36 functions. I exclude timing and allocator telemetry from this equality check.

## Application and execution boundary

I ran a real base-model request in an environment with the CPU-only PyTorch wheel. On the RTX 4070 SUPER I exercised base-only, adapter-only, display-only hybrid and conditioned hybrid through the browser. I verified the active badges, route text, copy action, desktop and mobile layouts, and the separate frontend error simulation. The live API confirmed the truthiness correction and base fallback when the configured adapter was missing. I retained genuine screenshots of the workbench. [Desktop](workbench.png) · [Mobile](workbench-mobile.png)

I checked the request handler, worker lifecycle, form rendering and model loader. The only accepted user fields are code and traceback. The worker tokenizes these strings and returns a structured diagnosis. A narrow truthiness correction inspects syntax and the supplied literal. Neither the HTTP process nor the model worker runs submitted code. The frontend renders model text through DOM text properties.

I moved the historical fixture builder's last host-side program execution into the benchmark's WASI guest and verified the generated rows against the archived fixtures. The guest gets no preopened directory, network capability or inherited environment. I tested denied filesystem reads and writes, socket creation, memory exhaustion and an unbounded loop. The runtime sets a 128 MiB memory limit, 300 million units of fuel, a three-second epoch deadline, one instance, one memory and bounded output. These controls apply to offline execution. [Sandbox implementation](../neuraldebugger/sandbox.py) · [Isolation tests](../tests/test_evaluation.py)

I require a digest-verified Qwen configuration, tokenizer and foundation safetensors. Remote model code is disabled. For LoRA, I supply the known architecture to PEFT and require local metadata, a matching model revision and a safetensors weight file. The release rejects legacy binary checkpoints, unrecognized adapter settings and missing files. The app's compatibility path returns an identified base fallback. The operator must control the project, adapter directories and installed Python environment.

## Dependency and rights review

I checked PyPI advisories against all 48 distributions in the audited Windows CPU environment. I updated the web framework, Starlette, Wasmtime, pytest and setuptools for this release. The final check still returned advisories for PyTorch 2.8.0, Transformers 4.55.4 and Accelerate 1.10.1. I retained the measured ML versions for reproducibility. The service uses a fixed Qwen architecture and revision, single-file safetensors, local adapter configuration and no uploaded checkpoints, trainer-state restores or user-selected model repositories. These constraints reduce exposure to reported model-loading issues. A dependency scan and local smoke tests cannot certify the stack for an internet-facing service. [PyTorch advisories](https://pypi.org/pypi/torch/2.8.0/json) · [Transformers advisories](https://pypi.org/pypi/transformers/4.55.4/json) · [Accelerate advisories](https://pypi.org/pypi/accelerate/1.10.1/json)

I checked the Qwen license at the pinned revision and the attribution for each of the 111 adapted MBPP records. Original project code and original dataset contributions use MIT. The measured adapter contribution and Qwen foundation use Apache-2.0. Adapted MBPP records retain CC BY 4.0 with source IDs and modification notices. The source repository distributes the adapter with its applicable license and credits. Users download the foundation and third-party dependencies from their publishers. [Third-party notices](../THIRD_PARTY.md) · [Dependency inventory](dependencies.md) · [Dataset card](../data/README.md)

## Repository and CI

I used Gitleaks 8.30.1 across all reachable refs with redaction enabled. It flagged 62 values in the release history. Sixty were the 30 repeated semantic-review identifiers in the masked packet and ratings. The other two were SHA-256 file digests in the pinned model manifest. I verified both against the independently downloaded tokenizer files. I recomputed each SHA-256 from the case ID, root cause and explanation, and verified that the ratings referenced those identifiers. I also inspected the complete reachable object inventory, commit metadata, path patterns, file sizes and binaries. The historical path-pattern matches in training fixtures were escaped Python newlines. The retained binary content consists of application screenshots, the measured loss figure and the verified adapter.

I pinned the checkout, Python and Node setup actions to upstream commit SHAs, used read-only repository permissions and disabled checkout credential persistence. I checked the workflow locally with actionlint 1.7.12 and exercised its test steps on Windows and Ubuntu 24.04. All 42 tests passed on each OS. Starlette issued one deprecation warning for the test client's HTTPX integration. JavaScript syntax checks passed. A GitHub-hosted workflow run requires publication. [Workflow](../.github/workflows/ci.yml)

I used OpenAI Codex to assist with the audit, code changes and documentation.
