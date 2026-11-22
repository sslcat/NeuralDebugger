# Dataset card

I froze a 176-program corpus for the local v2 trial. Each record carries a reproducible failure, a reference repair, a causal explanation, and a source identifier. I verified every reference on its full probe set and required every deliberately broken program to fail at least one probe. Programs supplied by the upstream corpus, reference code, and generated patches for v2 run in the restricted WASI interpreter.

| Partition | Programs | Behavioral probes | Original | Adapted MBPP |
|---|---:|---:|---:|---:|
| Training | 118 | 337 | 25 | 93 |
| Validation | 22 | 67 | 4 | 18 |
| Independent evaluation | 24 | 73 | 24 | 0 |
| Legacy evaluation | 12 | 36 | 12 | 0 |

I retained the legacy file byte-for-byte at SHA-256 `0933538b9be3df1368de629dd5b1a960c867f33388563ac35ece5f4a97ae3627`. I wrote the independent evaluation directly from new source programs and behavioral contracts, before examining predictions. It includes state persisting across calls, an exception handler overridden by finally, absent dictionary keys, bound-method and collection API mistakes, exclusive stops, and incorrect results with no Python exception. The harness supplies the failed input and expected/actual values for silent errors. Repeated-call probes evaluate the calls within one guest instance to expose mutable defaults. Each other probe starts with a fresh guest.

## Source and selection

I wrote the original fixtures for NeuralDebugger. For training and validation I also adapted 111 tasks from the sanitized Mostly Basic Python Problems corpus by Jacob Austin et al., Google Research. The source field contains the upstream task ID. Three adaptations originated in the pilot. For the new public examples I retained upstream contracts and executable comparisons, normalized the reference syntax, changed an operation, and generated a diagnosis identifying the changed expression. I verified the correction and observed the mutation failing. My original contributions use MIT. The MBPP adaptations retain CC BY 4.0 attribution. [Upstream snapshot](https://github.com/google-research/google-research/blob/f82046ba5aabbbb427dbfd38a254d26bff08b533/mbpp/sanitized-mbpp.json) · [Dataset license declaration](https://huggingface.co/datasets/google-research-datasets/mbpp) · [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)

I seeded the public task order, capped repeated transformations, screened for simple literal oracles, and retained at most one mutation per upstream task ID. I removed docstrings, normalized identifiers and constants, and compared structural token sequences from repaired and buggy programs. The cross-split threshold is a SequenceMatcher ratio of 0.91. I also reviewed algorithm families such as maximum products, rotations, power-of-two computations and subarrays. A family represented in validation stays out of training. I excluded a public swap task close in purpose to an evaluation case, one overlength example, and a near-duplicate original lookup. The manifest lists exclusions; transformation counts there describe candidates before final exclusions. Pairwise checks cover all six split pairs. [Split manifest](v2/manifest.json) · [Generator](../neuraldebugger/corpus.py)

I cannot establish zero pretraining overlap with public MBPP. Structural similarity cannot prove semantic independence, and three or four examples of behavior cannot specify every edge case of a program. Public mutations favor incorrect arithmetic and comparisons. Class-level results on the original evaluation programs have small denominators. I report those counts explicitly.

## Rebuild

Use Python 3.12, install the pinned project and benchmark packages, and fetch the WASI binary. Save the linked upstream JSON locally, then run `python -m neuraldebugger.corpus PATH_TO_SANITIZED_JSON`. The builder verifies source SHA-256 `ca95deaa9a01ef0a6f439f88bcf0dd3db3563d22f22aad6cae04ebb9a8d8c8e9`. It needs the pinned tokenizer for the sequence-length check. The training and validation JSONL are separate from both evaluation inputs. The older 39-case pilot remains available through `python -m neuraldebugger.data` and its original manifest.
