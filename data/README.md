# Dataset card

I built a 39-function Python debugging pilot. I wrote 36 original reference programs and normalized three short MBPP solutions. For each I specified a deterministic replacement, a mechanism description, a repair explanation, alternative root-cause terms, and concrete inputs with expected outputs. The compiler executes only these reviewed repository fixtures. It requires the reference to pass every check and the mutation to fail at least one. The first failure supplies the observed input and exception or expected/actual output. There are 91 checks across the dataset.

| Split | Independent programs | Purpose |
|---|---:|---|
| Train | 23 | Assistant-token supervision |
| Validation | 4 | Warm-up and epoch selection |
| Test | 12 | Frozen evaluation on 36 inputs |

I assign whole programs to splits before generating cases. I compare identifier-normalized reference syntax representations across splits and reject similarity at or above 0.965 using SequenceMatcher. One training candidate was removed during this check. Distinct programs can still share underlying error concepts. I have no way to audit overlap with Qwen's pretraining corpus.

The task covers wrong results and seven Python exception classes across the three splits. Every held-out program is original. Most inputs are short built-in types. This corpus has little coverage of multi-file applications, async behavior, or library-specific stack traces. Its size supports a low-cost feasibility experiment and limits generalization claims.

## Provenance

I adapted MBPP tasks 8 (squares), 12 (sorting matrix rows), and 14 (triangular-prism volume) from the sanitized release by Austin et al., Google Research. I changed formatting and supplied new mutations, tests and explanatory fields. These three records retain CC BY 4.0 attribution. The other 36 cases and my original dataset contributions use MIT. Each record carries its source and group. [Pinned MBPP source](https://github.com/google-research/google-research/blob/f82046ba5aabbbb427dbfd38a254d26bff08b533/mbpp/sanitized-mbpp.json) · [Dataset license](https://huggingface.co/datasets/google-research-datasets/mbpp) · [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)

Rebuild with Python 3.12 using `python -m neuraldebugger.data`. The manifest records the exact byte hash and row count of each output. The compiler source includes all authored fixtures for auditing. For a training pod, transfer only the compiled train and validation JSONL, their manifest, configuration and training modules. Leave the test JSONL and source specification with the evaluator.
