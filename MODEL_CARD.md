# NeuralDebugger model card

I use **Qwen/Qwen2.5-Coder-1.5B-Instruct**, revision **2e1fd397ee46e1388853d2af2c993145b0f1098a**, with the tokenizer and chat template from that same revision. I verified the downloaded safetensors SHA-256 as `c1b9b30e907950516ba3c646bdf570d8084c25a6410a0cdca80cf04b11bc13a8`. [Pinned upstream model](https://huggingface.co/Qwen/Qwen2.5-Coder-1.5B-Instruct/tree/2e1fd397ee46e1388853d2af2c993145b0f1098a)

## Selection

I wanted an instruction-tuned code model with enough Python ability to benchmark on a workstation. The 1.5B model has an Apache-2.0 license, native Transformers support, and fits CPU inference. Its pinned weights are 3,087,467,144 bytes. The direct Qwen2.5-Coder-3B-Instruct alternative requires more memory and carries the Qwen Research License. I evaluated the smaller model locally and downloaded only its weights. I have no head-to-head quality measurement for the 3B model. [1.5B model card](https://huggingface.co/Qwen/Qwen2.5-Coder-1.5B-Instruct) · [3B model card](https://huggingface.co/Qwen/Qwen2.5-Coder-3B-Instruct)

## Intended use and limitations

The model suggests explanations and candidate repairs for short Python functions and observed failures. The interface is designed for developer review. In the original 12-case baseline, two proposed fixes left their original bug intact. Other outputs repaired a function while giving inaccurate explanations of mutability, sort behavior or string truthiness. That pilot used three behavioral inputs per function. The dataset does not measure reliability across large repositories or unfamiliar packages. The model can follow misleading text embedded in a submission.

## Local v2 adapter

I trained a rank-8, alpha-16 LoRA adapter on query and value projections, using 118 training cases and 22 validation cases. I selected epoch 3 by validation loss (0.28985). The selected safetensors file is 4,372,840 bytes, SHA-256 96ac4f90bbf04f6c9e0d9ab67a99cac5fcb5d575f854866fc7c3ea57ff9ce92e. I include the measured checkpoint in `adapters/epoch-3` with its license and checksums. The checkpoint contains adapter weights; the pinned foundation model is loaded separately.

I kept the base backend as the default after reviewing the paired results. The adapter learned to label wrong results much more consistently. On the 24 independent cases, whole-function repairs fell from 20 to 16 and masked explanation scores fell from 1.17 to 0.54 out of 2. On the 12 legacy functions, whole-function repairs fell from 10 to 6. A falling validation loss captured how well the adapter reproduced the training-style answers. It did not predict improvement in behavioral repair. [Measured comparison](results/v2/comparison.md) · [All raw case reports](results/v2/case-reports.md)

To inspect this experiment locally, set ND_BACKEND to adapter and ND_ADAPTER to the selected epoch directory before starting the server. Missing or incompatible adapters trigger a labeled base fallback. I use display-only as an optional mode. Adapter-only and conditioned hybrid remain experimental. The pinned adapter is part of this local release candidate. [Four-mode results with latency and VRAM](results/hybrid/comparison.md) · [Mode configuration](docs/hybrid-usage.md)

## Model and data rights

Qwen supplies the foundation weights under Apache-2.0. I license the original NeuralDebugger implementation and original dataset contributions under MIT. The 111 adapted MBPP records in v2 carry CC BY 4.0 attribution. I distribute the learned adapter contribution under Apache-2.0 and include the Qwen and MBPP credits. Users download the foundation separately. [Adapter notices](adapters/README.md) [Notices](THIRD_PARTY.md) · [Data card](data/README.md)
