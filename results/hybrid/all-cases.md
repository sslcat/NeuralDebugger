# Paired case ledger

## rolling-total

Gold category: WrongResult. Classifier prediction: WrongResult.

| Arm | Checks | Reported category correct | Cause | Explanation |
|---|---:|---:|---:|---:|
| base | 3/3 | False | 0/2 | 0/2 |
| adapter | 3/3 | True | 0/2 | 1/2 |
| hybrid-display | 3/3 | True | 0/2 | 0/2 |
| hybrid-conditioned | 3/3 | True | 0/2 | 0/2 |

## pair-columns

Gold category: TypeError. Classifier prediction: TypeError.

| Arm | Checks | Reported category correct | Cause | Explanation |
|---|---:|---:|---:|---:|
| base | 1/3 | True | 1/2 | 0/2 |
| adapter | 1/3 | True | 0/2 | 0/2 |
| hybrid-display | 1/3 | True | 1/2 | 0/2 |
| hybrid-conditioned | 1/3 | True | 1/2 | 0/2 |

## queue-head

Gold category: IndexError. Classifier prediction: IndexError.

| Arm | Checks | Reported category correct | Cause | Explanation |
|---|---:|---:|---:|---:|
| base | 3/3 | True | 1/2 | 1/2 |
| adapter | 0/3 | True | 1/2 | 0/2 |
| hybrid-display | 3/3 | True | 1/2 | 1/2 |
| hybrid-conditioned | 0/3 | False | 0/2 | 0/2 |

## bucket-owners

Gold category: KeyError. Classifier prediction: KeyError.

| Arm | Checks | Reported category correct | Cause | Explanation |
|---|---:|---:|---:|---:|
| base | 3/3 | True | 2/2 | 2/2 |
| adapter | 1/3 | True | 0/2 | 0/2 |
| hybrid-display | 3/3 | True | 2/2 | 2/2 |
| hybrid-conditioned | 3/3 | True | 2/2 | 2/2 |

## text-parts

Gold category: ValueError. Classifier prediction: ValueError.

| Arm | Checks | Reported category correct | Cause | Explanation |
|---|---:|---:|---:|---:|
| base | 3/3 | True | 2/2 | 2/2 |
| adapter | 0/3 | False | 0/2 | 0/2 |
| hybrid-display | 3/3 | True | 2/2 | 2/2 |
| hybrid-conditioned | 1/3 | True | 2/2 | 0/2 |

## ordered-scores

Gold category: TypeError. Classifier prediction: TypeError.

| Arm | Checks | Reported category correct | Cause | Explanation |
|---|---:|---:|---:|---:|
| base | 3/3 | True | 1/2 | 0/2 |
| adapter | 3/3 | True | 0/2 | 1/2 |
| hybrid-display | 3/3 | True | 1/2 | 0/2 |
| hybrid-conditioned | 3/3 | True | 1/2 | 0/2 |

## half-open-span

Gold category: WrongResult. Classifier prediction: WrongResult.

| Arm | Checks | Reported category correct | Cause | Explanation |
|---|---:|---:|---:|---:|
| base | 3/3 | False | 2/2 | 2/2 |
| adapter | 3/3 | True | 2/2 | 2/2 |
| hybrid-display | 3/3 | True | 2/2 | 2/2 |
| hybrid-conditioned | 3/3 | True | 2/2 | 2/2 |

## rolling-mean

Gold category: ZeroDivisionError. Classifier prediction: ZeroDivisionError.

| Arm | Checks | Reported category correct | Cause | Explanation |
|---|---:|---:|---:|---:|
| base | 3/3 | True | 2/2 | 2/2 |
| adapter | 3/3 | True | 1/2 | 1/2 |
| hybrid-display | 3/3 | True | 2/2 | 2/2 |
| hybrid-conditioned | 3/3 | True | 2/2 | 2/2 |

## table-alias

Gold category: WrongResult. Classifier prediction: WrongResult.

| Arm | Checks | Reported category correct | Cause | Explanation |
|---|---:|---:|---:|---:|
| base | 3/3 | False | 2/2 | 2/2 |
| adapter | 1/3 | True | 1/2 | 0/2 |
| hybrid-display | 3/3 | True | 2/2 | 2/2 |
| hybrid-conditioned | 3/3 | True | 0/2 | 0/2 |

## consume-stream

Gold category: WrongResult. Classifier prediction: WrongResult.

| Arm | Checks | Reported category correct | Cause | Explanation |
|---|---:|---:|---:|---:|
| base | 1/3 | False | 2/2 | 1/2 |
| adapter | 0/3 | True | 0/2 | 0/2 |
| hybrid-display | 1/3 | True | 2/2 | 1/2 |
| hybrid-conditioned | 1/3 | True | 1/2 | 0/2 |

## field-number

Gold category: TypeError. Classifier prediction: TypeError.

| Arm | Checks | Reported category correct | Cause | Explanation |
|---|---:|---:|---:|---:|
| base | 3/3 | True | 2/2 | 2/2 |
| adapter | 3/3 | True | 0/2 | 1/2 |
| hybrid-display | 3/3 | True | 2/2 | 2/2 |
| hybrid-conditioned | 3/3 | True | 0/2 | 2/2 |

## predicate-call

Gold category: WrongResult. Classifier prediction: WrongResult.

| Arm | Checks | Reported category correct | Cause | Explanation |
|---|---:|---:|---:|---:|
| base | 3/3 | False | 0/2 | 1/2 |
| adapter | 3/3 | True | 0/2 | 0/2 |
| hybrid-display | 3/3 | True | 0/2 | 1/2 |
| hybrid-conditioned | 3/3 | True | 0/2 | 0/2 |

## seat-code

Gold category: WrongResult. Classifier prediction: WrongResult.

| Arm | Checks | Reported category correct | Cause | Explanation |
|---|---:|---:|---:|---:|
| base | 3/3 | False | 0/2 | 1/2 |
| adapter | 0/3 | False | 0/2 | 0/2 |
| hybrid-display | 3/3 | True | 0/2 | 1/2 |
| hybrid-conditioned | 3/3 | True | 2/2 | 2/2 |

## invoice-label

Gold category: TypeError. Classifier prediction: TypeError.

| Arm | Checks | Reported category correct | Cause | Explanation |
|---|---:|---:|---:|---:|
| base | 3/3 | True | 0/2 | 2/2 |
| adapter | 3/3 | True | 0/2 | 1/2 |
| hybrid-display | 3/3 | True | 0/2 | 2/2 |
| hybrid-conditioned | 3/3 | True | 2/2 | 2/2 |

## optional-alias

Gold category: KeyError. Classifier prediction: KeyError.

| Arm | Checks | Reported category correct | Cause | Explanation |
|---|---:|---:|---:|---:|
| base | 0/3 | False | 0/2 | 0/2 |
| adapter | 3/3 | True | 2/2 | 0/2 |
| hybrid-display | 0/3 | False | 0/2 | 0/2 |
| hybrid-conditioned | 0/3 | False | 0/2 | 0/2 |

## suffix-check

Gold category: AttributeError. Classifier prediction: AttributeError.

| Arm | Checks | Reported category correct | Cause | Explanation |
|---|---:|---:|---:|---:|
| base | 3/3 | True | 2/2 | 2/2 |
| adapter | 0/3 | False | 0/2 | 0/2 |
| hybrid-display | 3/3 | True | 2/2 | 2/2 |
| hybrid-conditioned | 3/3 | True | 2/2 | 2/2 |

## last-neighbor

Gold category: IndexError. Classifier prediction: IndexError.

| Arm | Checks | Reported category correct | Cause | Explanation |
|---|---:|---:|---:|---:|
| base | 3/3 | False | 1/2 | 2/2 |
| adapter | 3/3 | True | 0/2 | 1/2 |
| hybrid-display | 3/3 | True | 1/2 | 2/2 |
| hybrid-conditioned | 3/3 | True | 2/2 | 2/2 |

## parse-rate

Gold category: ValueError. Classifier prediction: ValueError.

| Arm | Checks | Reported category correct | Cause | Explanation |
|---|---:|---:|---:|---:|
| base | 3/3 | True | 1/2 | 2/2 |
| adapter | 3/3 | True | 0/2 | 1/2 |
| hybrid-display | 3/3 | True | 1/2 | 2/2 |
| hybrid-conditioned | 3/3 | True | 1/2 | 2/2 |

## call-notes

Gold category: WrongResult. Classifier prediction: WrongResult.

| Arm | Checks | Reported category correct | Cause | Explanation |
|---|---:|---:|---:|---:|
| base | 3/3 | False | 1/2 | 2/2 |
| adapter | 1/3 | True | 0/2 | 0/2 |
| hybrid-display | 3/3 | True | 1/2 | 2/2 |
| hybrid-conditioned | 3/3 | True | 1/2 | 1/2 |

## range-band

Gold category: WrongResult. Classifier prediction: WrongResult.

| Arm | Checks | Reported category correct | Cause | Explanation |
|---|---:|---:|---:|---:|
| base | 4/4 | False | 1/2 | 0/2 |
| adapter | 1/4 | True | 0/2 | 0/2 |
| hybrid-display | 4/4 | True | 1/2 | 0/2 |
| hybrid-conditioned | 4/4 | True | 1/2 | 0/2 |

## comments

Gold category: WrongResult. Classifier prediction: WrongResult.

| Arm | Checks | Reported category correct | Cause | Explanation |
|---|---:|---:|---:|---:|
| base | 1/3 | False | 1/2 | 0/2 |
| adapter | 3/3 | True | 0/2 | 1/2 |
| hybrid-display | 1/3 | True | 1/2 | 0/2 |
| hybrid-conditioned | 0/3 | True | 0/2 | 0/2 |

## nested-config

Gold category: KeyError. Classifier prediction: KeyError.

| Arm | Checks | Reported category correct | Cause | Explanation |
|---|---:|---:|---:|---:|
| base | 3/3 | True | 2/2 | 2/2 |
| adapter | 3/3 | True | 2/2 | 1/2 |
| hybrid-display | 3/3 | True | 2/2 | 2/2 |
| hybrid-conditioned | 3/3 | True | 2/2 | 2/2 |

## trim-extension

Gold category: WrongResult. Classifier prediction: WrongResult.

| Arm | Checks | Reported category correct | Cause | Explanation |
|---|---:|---:|---:|---:|
| base | 3/3 | False | 1/2 | 2/2 |
| adapter | 2/3 | True | 0/2 | 0/2 |
| hybrid-display | 3/3 | True | 1/2 | 2/2 |
| hybrid-conditioned | 3/3 | True | 0/2 | 2/2 |

## parallel-lists

Gold category: IndexError. Classifier prediction: IndexError.

| Arm | Checks | Reported category correct | Cause | Explanation |
|---|---:|---:|---:|---:|
| base | 3/3 | True | 2/2 | 2/2 |
| adapter | 3/3 | True | 0/2 | 1/2 |
| hybrid-display | 3/3 | True | 2/2 | 2/2 |
| hybrid-conditioned | 0/3 | False | 0/2 | 0/2 |

## set-growth

Gold category: AttributeError. Classifier prediction: AttributeError.

| Arm | Checks | Reported category correct | Cause | Explanation |
|---|---:|---:|---:|---:|
| base | 3/3 | True | 2/2 | 2/2 |
| adapter | 3/3 | True | 2/2 | 2/2 |
| hybrid-display | 3/3 | True | 2/2 | 2/2 |
| hybrid-conditioned | 3/3 | True | 2/2 | 2/2 |

## sign-column

Gold category: WrongResult. Classifier prediction: WrongResult.

| Arm | Checks | Reported category correct | Cause | Explanation |
|---|---:|---:|---:|---:|
| base | 3/3 | False | 0/2 | 0/2 |
| adapter | 1/3 | True | 0/2 | 0/2 |
| hybrid-display | 3/3 | True | 0/2 | 0/2 |
| hybrid-conditioned | 1/3 | True | 1/2 | 0/2 |

## row-decode

Gold category: TypeError. Classifier prediction: TypeError.

| Arm | Checks | Reported category correct | Cause | Explanation |
|---|---:|---:|---:|---:|
| base | 3/3 | True | 1/2 | 0/2 |
| adapter | 3/3 | True | 1/2 | 0/2 |
| hybrid-display | 3/3 | True | 1/2 | 0/2 |
| hybrid-conditioned | 3/3 | True | 0/2 | 0/2 |

## veto-finally

Gold category: WrongResult. Classifier prediction: WrongResult.

| Arm | Checks | Reported category correct | Cause | Explanation |
|---|---:|---:|---:|---:|
| base | 3/3 | False | 1/2 | 0/2 |
| adapter | 3/3 | True | 1/2 | 1/2 |
| hybrid-display | 3/3 | True | 1/2 | 0/2 |
| hybrid-conditioned | 3/3 | True | 0/2 | 1/2 |

## width-padding

Gold category: WrongResult. Classifier prediction: WrongResult.

| Arm | Checks | Reported category correct | Cause | Explanation |
|---|---:|---:|---:|---:|
| base | 1/3 | False | 0/2 | 0/2 |
| adapter | 1/3 | True | 0/2 | 0/2 |
| hybrid-display | 1/3 | True | 0/2 | 0/2 |
| hybrid-conditioned | 0/3 | False | 0/2 | 0/2 |

## index-or-zero

Gold category: WrongResult. Classifier prediction: WrongResult.

| Arm | Checks | Reported category correct | Cause | Explanation |
|---|---:|---:|---:|---:|
| base | 3/3 | False | 0/2 | 1/2 |
| adapter | 3/3 | True | 0/2 | 0/2 |
| hybrid-display | 3/3 | True | 0/2 | 1/2 |
| hybrid-conditioned | 2/3 | True | 0/2 | 0/2 |

## step-chunks

Gold category: WrongResult. Classifier prediction: WrongResult.

| Arm | Checks | Reported category correct | Cause | Explanation |
|---|---:|---:|---:|---:|
| base | 1/3 | False | 1/2 | 0/2 |
| adapter | 3/3 | True | 2/2 | 1/2 |
| hybrid-display | 1/3 | True | 1/2 | 0/2 |
| hybrid-conditioned | 1/3 | True | 0/2 | 0/2 |

## call-count

Gold category: WrongResult. Classifier prediction: WrongResult.

| Arm | Checks | Reported category correct | Cause | Explanation |
|---|---:|---:|---:|---:|
| base | 3/3 | False | 1/2 | 1/2 |
| adapter | 3/3 | True | 0/2 | 0/2 |
| hybrid-display | 3/3 | True | 1/2 | 1/2 |
| hybrid-conditioned | 3/3 | True | 1/2 | 1/2 |

## pair-swap

Gold category: WrongResult. Classifier prediction: WrongResult.

| Arm | Checks | Reported category correct | Cause | Explanation |
|---|---:|---:|---:|---:|
| base | 3/3 | False | 2/2 | 1/2 |
| adapter | 3/3 | True | 0/2 | 1/2 |
| hybrid-display | 3/3 | True | 2/2 | 1/2 |
| hybrid-conditioned | 3/3 | True | 1/2 | 1/2 |

## suffix-mass

Gold category: TypeError. Classifier prediction: TypeError.

| Arm | Checks | Reported category correct | Cause | Explanation |
|---|---:|---:|---:|---:|
| base | 3/3 | True | 1/2 | 2/2 |
| adapter | 3/3 | True | 0/2 | 1/2 |
| hybrid-display | 3/3 | True | 1/2 | 2/2 |
| hybrid-conditioned | 3/3 | True | 2/2 | 1/2 |

## metadata-items

Gold category: AttributeError. Classifier prediction: AttributeError.

| Arm | Checks | Reported category correct | Cause | Explanation |
|---|---:|---:|---:|---:|
| base | 3/3 | True | 1/2 | 2/2 |
| adapter | 3/3 | True | 2/2 | 1/2 |
| hybrid-display | 3/3 | True | 1/2 | 2/2 |
| hybrid-conditioned | 3/3 | True | 1/2 | 0/2 |

## rfind-missing

Gold category: WrongResult. Classifier prediction: WrongResult.

| Arm | Checks | Reported category correct | Cause | Explanation |
|---|---:|---:|---:|---:|
| base | 3/3 | False | 1/2 | 2/2 |
| adapter | 2/3 | True | 0/2 | 0/2 |
| hybrid-display | 3/3 | True | 1/2 | 2/2 |
| hybrid-conditioned | 3/3 | True | 1/2 | 1/2 |
