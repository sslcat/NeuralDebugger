# Measured LoRA adapter

I include the epoch-3 checkpoint that produced the adapter and hybrid results. Its 4,372,840-byte safetensors file contains 1,089,536 learned LoRA parameters. The SHA-256 digest is `96ac4f90bbf04f6c9e0d9ab67a99cac5fcb5d575f854866fc7c3ea57ff9ce92e`. The base model and tokenizer come from the separately downloaded Qwen revision recorded in the metadata. The manifest covers the tensors and both configuration files. I normalized JSON line endings for cross-platform checkouts.

I distribute my adapter contribution under Apache License 2.0. It was trained with Qwen Team's Apache-2.0 Qwen2.5-Coder-1.5B-Instruct and with original fixtures and adapted Mostly Basic Python Problems examples by Jacob Austin et al., Google Research. The data card records task IDs, source, changes and CC BY 4.0 attribution. Keep these credits and the applicable license notices with redistributions. [Adapter license](LICENSE) · [Model card](../MODEL_CARD.md) · [Dataset attribution](../data/README.md)

From the project root I verify the checkpoint with `python -m tools.artifacts verify adapters/epoch-3`. I set `ND_ADAPTER=adapters/epoch-3` for adapter-backed modes. A newly trained checkpoint can be used in the workbench. The archived experiment tables refer specifically to the digest above.
