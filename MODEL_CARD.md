# NeuralDebugger model card

I use **Qwen/Qwen2.5-Coder-1.5B-Instruct**, revision **2e1fd397ee46e1388853d2af2c993145b0f1098a**, with the tokenizer and chat template from that same revision. I verified the downloaded safetensors SHA-256 as `c1b9b30e907950516ba3c646bdf570d8084c25a6410a0cdca80cf04b11bc13a8`. [Pinned upstream model](https://huggingface.co/Qwen/Qwen2.5-Coder-1.5B-Instruct/tree/2e1fd397ee46e1388853d2af2c993145b0f1098a)

## Selection

I wanted an instruction-tuned code model with enough Python ability to benchmark on a workstation. The 1.5B model has an Apache-2.0 license, native Transformers support, and fits CPU inference. Its pinned weights are 3,087,467,144 bytes. The direct Qwen2.5-Coder-3B-Instruct alternative requires more memory and carries the Qwen Research License. I evaluated the smaller model locally and downloaded only its weights. I have no head-to-head quality measurement for the 3B model. [1.5B model card](https://huggingface.co/Qwen/Qwen2.5-Coder-1.5B-Instruct) · [3B model card](https://huggingface.co/Qwen/Qwen2.5-Coder-3B-Instruct)

## Intended use and limitations

The model suggests explanations and candidate repairs for short Python functions and observed failures. The interface is designed for developer review. In 12 held-out cases, two proposed fixes left their original bug intact. Other outputs repaired a function while giving inaccurate explanations of mutability, sort behavior or string truthiness. Each case has only three behavioral inputs. The dataset does not measure reliability across large repositories or unfamiliar packages. The model can follow misleading text embedded in a submission.

The current default is the original model. A local one-update CPU LoRA checkpoint exists for integration verification. It targets query and value projections with rank 8. The checkpoint contains 1,089,536 trainable parameters and occupies 4,372,840 bytes in safetensors form. I verified its digest, reloaded it and observed a numerical effect on one validation example. I have not selected it as a release model. Main-run adapters, downstream superiority and cloud training costs remain unmeasured.

## Model and data rights

Qwen supplies the foundation weights under Apache-2.0. I license the original NeuralDebugger implementation and original dataset contributions under MIT. The three adapted MBPP records carry CC BY 4.0 attribution. No pretrained weights or adapter tensors are included in the Git history. Any future adapter release will require a final review of upstream notices, data attribution, provenance and the release approval. [Notices](THIRD_PARTY.md) · [Data card](data/README.md)
