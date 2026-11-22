# Evaluation

For the expanded local experiment I froze two evaluation sets, scored repairs with executable probes, and graded root cause and explanation separately under masked model identities. The case-level proxy described below belongs to the original pilot. [Local paired protocol](v2-protocol.md) · [Measured comparison](../results/v2/comparison.md)

## Hybrid comparison

I froze the short classifier and both repair paths on validation before scoring the same 36 held-out programs. I measured all four configurations again on the RTX 4070 SUPER, including standalone baselines. I compared classification before and after repair parsing and tracked individual gains and losses from supplying the hint. [Protocol](hybrid-protocol.md) · [Wrong-hint control](hybrid-sensitivity.md) · [Four-arm results](../results/hybrid/comparison.md)

On the independent suite, attaching the classifier label to a base repair preserved 20/24 complete repairs. Passing the label into the repair prompt reduced that to 17/24. On the legacy suite the counts were 10/12 and 8/12. I found no fully repaired program gained by supplying the hint in either suite.

All 36 naturally predicted labels were correct, including those on regressions. In `parallel-lists`, the conditioned repair response failed JSON parsing. In `sign-column`, the proposed integer filter left the incorrect sign calculation in place. In `index-or-zero`, the suggested handler assumed that a call to `next` with a default could raise `StopIteration` when the target was absent. On the legacy header parser, the conditioned repair returned an empty list for values containing a colon. Its tests required preserving the whole value following the first colon.

I can measure the effect of providing a correct hint on these programs, but this sample gives me no natural misclassification cases from which to estimate harm. My separate, predeclared validation intervention supplies incorrect categories on six fixed cases. The full ledger includes every failure and the underlying predictions retain both the first-stage label and the base repairer's raw response. [Case ledger](../results/hybrid/all-cases.md) · [Raw predictions and telemetry](../results/hybrid/)

I observed a 12.5 percentage-point drop in independent complete repairs from conditioning on the label. The paired 95% bootstrap interval was -25 to 0 points. Display-only reproduced every base repair and explanation byte-for-byte. Independent median latency was 6.77 seconds for base, 4.82 for the adapter, 9.36 for display-only and 6.52 for conditioned. Their warmed peak allocations ranged from 2.905 to 2.911 GiB. Wall time includes model generation and parsing. Other workstation activity and different answer lengths limit the timing comparison.

On the six validation controls, the base repair passed 12/17 probes without a hint, 12/17 with the correct hint and 8/17 with a deliberately wrong hint. The corresponding complete-repair counts were 3, 2 and 2. Changing only the hint from correct to wrong lost two complete repairs and gained two different ones. For `mbpp-92`, the false IndexError hint led to a patch that shortened the loop to avoid a supposed indexing error, and passing probes fell from three to one. The same intervention improved `mbpp-415` from two passing probes to three. I treat these six cases as a sensitivity check. They do not estimate how often the classifier will make mistakes on new programs.

I replayed the complete matrix in a fresh installation during the release audit. With the included epoch-3 adapter, all 144 responses matched the archived repair text, classifier output, parsed diagnosis and behavioral scores. All 36 display-only repairs matched base-only byte for byte. Latency and allocator measurements depend on the run and are excluded from byte-level comparisons. [Release audit](release-audit.md) · [Replay verifier](../tools/verify_replay.py)

## Original pilot protocol

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
