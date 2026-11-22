# Training method

I selected supervised LoRA on the 1.5B Qwen coder. Its frozen weights occupy roughly 3.1 GB at two bytes per parameter, before activations and runtime overhead. A 16 GB GPU gives this short-sequence adapter experiment room without an additional quantization dependency. The local smoke test and a cloud experiment have different purposes. I keep a one-update smoke adapter out of product defaults.

I pinned the model, tokenizer, seed and package versions. The chat encoder masks prompt labels, checks exact token boundaries and rejects overflow. The current 27 training and validation examples use at most 257 tokens under the 768-token training limit. The optimizer visits a seeded permutation each epoch. I update query and value projections with rank 8, alpha 16 and dropout 0.05. Batch size is one with accumulation over four cases, AdamW learning rate 0.00015, weight decay 0.01, and gradient norm limit 1. Three full epochs would produce 18 optimizer updates. I save an adapter after each epoch, record step loss, elapsed seconds, and peak CUDA allocation, and select the lowest mean validation loss. No test predictions enter the selection.

```bash
python -m tools.artifacts bundle .runs/training-inputs.zip
python -m neuraldebugger.train --smoke --out .runs/smoke
python -m tools.artifacts verify .runs/smoke/epoch-1
python -m neuraldebugger.train --out .runs/main
```

Start the main command only after reviewing the approved preflight, smoke artifact, remaining budget and live watchdog. Each command requires a fresh output directory. Epoch directories are inference checkpoints. Restarting a training run starts a new optimizer trajectory. For a reproducible experiment I retain the complete JSONL training log, best-epoch pointer, adapter configuration, model metadata, verified weight file, and the environment manifest. I keep the smoke and main directories separate.

For a pod I would use the official PyTorch 2.8 CUDA 12.8 template, check the image digest and CUDA compatibility during preflight, and install the pinned user-space dependencies. I would unpack the training-only payload onto the temporary container disk. The experiment needs no network volume, persistent mount, paid API or service endpoint. After the smoke and main jobs, the controller host must recover artifacts over SSH, run the local checksum and tensor checks, then signal recovery. A failed transfer is a failure path with a deadline. It cannot extend the cost cutoff.

I evaluate the selected adapter back on the same local machine and decoding protocol as the baseline. The base backend remains the default until a review of paired cases supports adopting an adapter. A single optimizer update, even with finite loss, is only a pipeline check.
