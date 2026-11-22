# Hybrid evaluation

I reran all four arms on the local RTX 4070 SUPER. Repair counts require every behavioral probe to pass. I scored the raw diagnosis prose on a 0–2 scale. I count a missing or unparseable diagnosis as a classification miss and score a parseable category even if its program is unusable. The standalone classifier is also scored before repair parsing.

## Legacy · 12 programs

| Configuration | Complete repairs | Passing probes | Category correct | Mean cause | Mean explanation | Invalid | Median seconds | Peak allocated GiB | Peak reserved GiB |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| base | 10/12 | 32/36 | 7/12 | 1.42 | 1.25 | 0/12 | 7.60 | 2.903 | 2.939 |
| adapter | 6/12 | 21/36 | 11/12 | 0.42 | 0.50 | 1/12 | 3.01 | 2.903 | 2.939 |
| hybrid-display | 10/12 | 32/36 | 12/12 | 1.42 | 1.25 | 0/12 | 6.95 | 2.907 | 2.941 |
| hybrid-conditioned | 8/12 | 27/36 | 11/12 | 0.92 | 0.67 | 1/12 | 5.74 | 2.907 | 2.939 |

The category-only decode matched 12/12 gold categories. The display-only repair text matched the standalone base output byte-for-byte on 12/12.

| Classifier result | Programs | Display repairs | Conditioned repairs | Gains | Losses |
|---|---:|---:|---:|---:|---:|
| Correct | 12 | 10 | 8 | 0 | 2 |
| Incorrect or missing | 0 | 0 | 0 | 0 | 0 |

The conditioned-minus-base repair-rate difference has a paired 95% bootstrap interval of [-41.7, +0.0] percentage points.

## Independent · 24 programs

| Configuration | Complete repairs | Passing probes | Category correct | Mean cause | Mean explanation | Invalid | Median seconds | Peak allocated GiB | Peak reserved GiB |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| base | 20/24 | 64/73 | 9/24 | 0.96 | 1.17 | 1/24 | 6.77 | 2.905 | 2.939 |
| adapter | 16/24 | 56/73 | 22/24 | 0.50 | 0.54 | 2/24 | 4.82 | 2.907 | 2.939 |
| hybrid-display | 20/24 | 64/73 | 23/24 | 0.96 | 1.17 | 1/24 | 9.36 | 2.909 | 2.941 |
| hybrid-conditioned | 17/24 | 56/73 | 21/24 | 0.92 | 0.92 | 3/24 | 6.52 | 2.911 | 2.941 |

The category-only decode matched 24/24 gold categories. The display-only repair text matched the standalone base output byte-for-byte on 24/24.

| Classifier result | Programs | Display repairs | Conditioned repairs | Gains | Losses |
|---|---:|---:|---:|---:|---:|
| Correct | 24 | 20 | 17 | 0 | 3 |
| Incorrect or missing | 0 | 0 | 0 | 0 | 0 |

The conditioned-minus-base repair-rate difference has a paired 95% bootstrap interval of [-25.0, +0.0] percentage points.

## Deliberately wrong validation hints

| Validation program | No hint | Correct hint | Wrong hint |
|---|---:|---:|---:|
| document-title | 1/2 | 1/2 | 1/2 |
| mbpp-577 | 3/3 | 2/3 | 3/3 |
| mbpp-92 | 3/3 | 3/3 | 1/3 |
| mbpp-120 | 3/3 | 3/3 | 0/3 |
| mbpp-415 | 2/3 | 2/3 | 3/3 |
| mbpp-138 | 0/3 | 1/3 | 0/3 |

## Device-wide telemetry

I sampled the entire GPU once per second, including model loading, behavioral scoring and activity from other applications. The suite tables above give process-specific PyTorch peaks during warmed inference.

| Configuration | Samples | Mean GPU utilization | Peak memory used, MiB |
|---|---:|---:|---:|
| base | 294 | 36.7% | 8142 |
| adapter | 178 | 38.4% | 8012 |
| hybrid-display | 337 | 36.2% | 8015 |
| hybrid-conditioned | 264 | 42.2% | 7243 |

I used one masked, AI-assisted reviewer for root cause and explanation. I reused scores for identical prose on the same program. The summary file contains results by category and paired intervals for each metric. [Machine-readable summary](summary.json) · [Every held-out case](all-cases.md)
