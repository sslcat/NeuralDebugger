# Local paired evaluation

I scored raw outputs from the RTX 4070 SUPER. The independent suite is the primary outcome. Scores for cause and explanation come from one masked AI-assisted reviewer on a 0–2 scale. All intervals below resample paired programs.

## Test (12 programs)

| Metric | Base | Adapter | Change | Paired 95% interval for change |
|---|---:|---:|---:|---:|
| repair | 0.833 | 0.500 | -0.333 | [-0.583, -0.083] |
| checks | 0.889 | 0.583 | -0.306 | [-0.528, -0.083] |
| category | 0.583 | 0.917 | +0.333 | [+0.000, +0.667] |
| invalid | 0.000 | 0.083 | +0.083 | [+0.000, +0.250] |
| cause | 1.417 | 0.417 | -1.000 | [-1.417, -0.583] |
| explanation | 1.250 | 0.500 | -0.750 | [-1.333, -0.167] |
| seconds | 3.571 | 2.273 | -1.297 | [-1.555, -0.688] |

| Gold category | n | Patches passing (base → adapter) | Categories correct | Mean cause | Mean explanation |
|---|---:|---:|---:|---:|---:|
| IndexError | 1 | 1 → 0 | 1 → 1 | 1.00 → 1.00 | 1.00 → 0.00 |
| KeyError | 1 | 1 → 0 | 1 → 1 | 2.00 → 0.00 | 2.00 → 0.00 |
| TypeError | 3 | 2 → 2 | 3 → 3 | 1.33 → 0.00 | 0.67 → 0.67 |
| ValueError | 1 | 1 → 0 | 1 → 0 | 2.00 → 0.00 | 2.00 → 0.00 |
| WrongResult | 5 | 4 → 3 | 0 → 5 | 1.20 → 0.60 | 1.20 → 0.60 |
| ZeroDivisionError | 1 | 1 → 1 | 1 → 1 | 2.00 → 1.00 | 2.00 → 1.00 |

Cases failing at least one behavioral probe in either arm: pair-columns, queue-head, bucket-owners, text-parts, table-alias, consume-stream.

## Independent (24 programs)

| Metric | Base | Adapter | Change | Paired 95% interval for change |
|---|---:|---:|---:|---:|
| repair | 0.833 | 0.667 | -0.167 | [-0.417, +0.083] |
| checks | 0.877 | 0.767 | -0.110 | [-0.301, +0.083] |
| category | 0.375 | 0.917 | +0.542 | [+0.292, +0.750] |
| invalid | 0.042 | 0.083 | +0.042 | [-0.083, +0.167] |
| cause | 0.958 | 0.500 | -0.458 | [-0.833, -0.083] |
| explanation | 1.167 | 0.542 | -0.625 | [-1.000, -0.250] |
| seconds | 3.820 | 3.070 | -0.750 | [-1.070, -0.328] |

| Gold category | n | Patches passing (base → adapter) | Categories correct | Mean cause | Mean explanation |
|---|---:|---:|---:|---:|---:|
| AttributeError | 3 | 3 → 2 | 3 → 2 | 1.67 → 1.33 | 2.00 → 1.00 |
| IndexError | 2 | 2 → 2 | 1 → 2 | 1.50 → 0.00 | 2.00 → 1.00 |
| KeyError | 2 | 1 → 2 | 1 → 2 | 1.00 → 2.00 | 1.00 → 0.50 |
| TypeError | 3 | 3 → 3 | 3 → 3 | 0.67 → 0.33 | 1.33 → 0.67 |
| ValueError | 1 | 1 → 1 | 1 → 1 | 1.00 → 0.00 | 2.00 → 1.00 |
| WrongResult | 13 | 10 → 6 | 0 → 12 | 0.77 → 0.23 | 0.77 → 0.31 |

Cases failing at least one behavioral probe in either arm: seat-code, optional-alias, suffix-check, call-notes, range-band, comments, trim-extension, sign-column, width-padding, step-chunks, rfind-missing.
