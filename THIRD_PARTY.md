# Third-party notices

I distribute original NeuralDebugger code under MIT. The repository references third-party software and model artifacts downloaded separately.

- Qwen Team, Qwen2.5-Coder-1.5B-Instruct, Apache License 2.0. The tokenizer uses the model repository at the same commit. The foundation weights are excluded from Git. Preserve upstream licensing and attribution when redistributing model artifacts. [Model and license](https://huggingface.co/Qwen/Qwen2.5-Coder-1.5B-Instruct/tree/2e1fd397ee46e1388853d2af2c993145b0f1098a)
- Jacob Austin et al., Google Research, Mostly Basic Python Problems, CC BY 4.0. The v2 corpus contains 111 adapted records with upstream task IDs, including the three pilot adaptations. Modifications comprise formatting, debugging mutations, observations and annotations. The new public examples retain the upstream test comparisons. [Source and attribution](data/README.md)
- VMware Labs, WebAssembly Language Runtimes, CPython 3.12.0 WASI distribution. The fetched binary carries Python and bundled component licenses. Wasmtime is provided by the Bytecode Alliance under Apache-2.0 with LLVM exception. The benchmark downloads the interpreter separately. [Runtime release](https://github.com/vmware-labs/webassembly-language-runtimes/releases/tag/python%2F3.12.0%2B20231211-040d5a6) · [Python licensing](https://docs.python.org/3/license.html) · [Wasmtime license](https://github.com/bytecodealliance/wasmtime/blob/main/LICENSE)

I used PyTorch, Hugging Face Transformers and PEFT, FastAPI, Pydantic, Uvicorn and their dependencies under their respective upstream licenses. Original UI assets are HTML, CSS, and text. No externally hosted fonts or analytics are required.
