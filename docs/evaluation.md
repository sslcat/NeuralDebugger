# Evaluation protocol

I freeze the prompt, test bytes, decoding settings, parser and scorer before training. Each run loads the same model revision, warms up on the first validation case, then generates once per test case in file order. The model sees the buggy function and one observed failure. Additional checks, anchors, and references stay with the scorer. I use greedy decoding with one beam, a 1,536-token input budget, and a 384-token output cap. The adapter command fails if the requested adapter cannot load.

| Measure | Operational definition |
|---|---|
| Category accuracy | Exact case-insensitive match to the exception class or WrongResult. The exception name often appears in the input. |
| Root-cause identification proxy | All prewritten groups of alternative mechanism terms occur in the root-cause field. A synonym can score zero and a negated statement can score one. |
| Fix correctness | Fraction of cases whose patch passes every behavioral check. |
| Executable pass rate | Passing inputs divided by all inputs, including invalid responses in the denominator. |
| Reference AST match | Identical syntax trees after discarding source locations. Alternative correct implementations can score zero. |
| Explanation rubric, 0–2 | One point for the mechanism proxy in the diagnosis. One for a distinct explanation containing a predeclared repair-action word. This measures surface features. The case report permits semantic review. |
| Invalid or unusable | Malformed schema, unparsable Python, or missing the requested top-level function. A syntactically valid wrong answer counts as an incorrect fix. |
| Latency | Wall-clock seconds for tokenization, generation, and decoding after one warm-up. I report the median and retain every duration. |

The parser accepts either the JSON object or a single enclosing Markdown fence. I keep raw text even when parsing fails. The report shows reference diagnoses and model text for every case. A manual explanation review can score 0 for wrong or missing, 1 for identifying the failure without a sound repair rationale, and 2 for a correct mechanism and repair rationale. I keep any such review separate from the automatic rubric.

## Executing a patch

I run behavioral checks only in the offline evaluator. Each input gets a fresh CPython 3.12 WebAssembly instance with a 128 MiB linear-memory ceiling, a 300 million instruction-fuel budget, a three-second epoch deadline and bounded output. There are no guest filesystem directories, inherited environment variables, sockets, or host standard streams. The host parses a bounded literal and compares the result with the expected value outside the guest. An isolated runtime can have interpreter differences and limited libraries. These fixtures use Python built-ins. Run the sandbox self-tests before accepting measurements.

```bash
python tools/fetch_sandbox.py
python -m pytest -q
python -m neuraldebugger.evaluate --out results/base-new
python -m neuraldebugger.evaluate --adapter PATH_TO_ADAPTER --out results/tuned-new
python -m neuraldebugger.compare results/base-new results/tuned-new
```

The evaluator creates a fresh output directory and refuses to overwrite earlier predictions. If isolation is unavailable, the explicit `--skip-execution` option leaves behavioral metrics null. I reject comparisons across different sandbox settings, benchmark digests, model revisions, or devices. Use the same hardware and thread settings for timing.

The paired comparison reports every case, absolute differences, relative changes where the baseline denominator is nonzero, and percentile intervals from 2,000 seeded resamples of whole cases. Inputs within one function stay together. With 12 small functions these intervals describe sampling uncertainty within this pilot. They cannot establish performance on arbitrary projects.
