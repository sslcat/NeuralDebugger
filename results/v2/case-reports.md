# All paired cases

## rolling-total

Unary plus assigns each current value to total and discards the previous sum.

```python
def running(values):
    out = []
    total = 0
    for value in values:
        total =+ value
        out.append(total)
    return out
```

```text
running([2, 3, -1])
AssertionError: expected [2, 5, 4], observed [2, 3, -1]
```

**Base** — 3/3 behavioral checks; cause 0/2, explanation 0/2.

`````text
```json
{
  "category": "AssertionError",
  "root_cause": "The `+=` operator is used incorrectly in the loop. It should be `total += value` to add the current value to the total.",
  "corrected_code": "def running(values):\n    out = []\n    total = 0\n    for value in values:\n        total += value\n        out.append(total)\n    return out",
  "explanation": "The original code uses `+=`, which is incorrect because it modifies the variable `total` directly within the loop. This can lead to unexpected behavior if `total` is modified elsewhere in the function. The correct way to add the current value to `total` is by using `total += value`. "
}
```
`````

**Adapter** — 3/3 behavioral checks; cause 0/2, explanation 1/2.

`````text
{"category": "WrongResult", "root_cause": "The expression 'total =+ value' adds instead of assigns.", "corrected_code": "def running(values):\n    out = []\n    total = 0\n    for value in values:\n        total += value\n        out.append(total)\n    return out", "explanation": "Use 'total += value' at that operation to restore the intended addition."}
`````

Review: Both misdescribe =+. B names the correct edit but reverses what the original assignment does.

## pair-columns

Enumerate supplies an index and an entire pair, so addition mixes an integer and a list.

```python
def columns(rows):
    return [left + right for left, right in enumerate(rows)]
```

```text
columns([[3, 5], [1, 2]])
TypeError: unsupported operand type(s) for +: 'int' and 'list'
```

**Base** — 1/3 behavioral checks; cause 1/2, explanation 0/2.

`````text
```json
{
  "category": "TypeError",
  "root_cause": "The `+` operator cannot be used to add an integer to a list.",
  "corrected_code": "def columns(rows):\n    return [str(left) + str(right) for left, right in enumerate(rows)]",
  "explanation": "In the original code, `left + right` is trying to concatenate an integer (`left`) with a list (`right`). This operation is not supported because integers and lists are of different types. The corrected code converts both `left` and `right` to strings before concatenating them, allowing the operation to proceed."
}
```
`````

Failed inputs and expected values

```text
columns([[3, 5], [1, 2]]) -> [8, 3]
columns([[0, -2]]) -> [-2]
```

**Adapter** — 1/3 behavioral checks; cause 0/2, explanation 0/2.

`````text
{"category": "TypeError", "root_cause": "The expression 'left + right' adds operands where multiplication is required.", "corrected_code": "def columns(rows):\n    return [left * right for left, right in enumerate(rows)]", "explanation": "Use 'left * right' at that operation to restore the intended multiplication."}
`````

Failed inputs and expected values

```text
columns([[3, 5], [1, 2]]) -> [8, 3]
columns([[0, -2]]) -> [-2]
```

Review: B identifies mixed operand types but converting to strings loses the numeric row-sum contract. A invents multiplication.

## queue-head

The guard is reversed, allowing an empty list to reach the first-element lookup.

```python
def next_job(jobs):
    if jobs:
        return None
    return jobs[0]
```

```text
next_job([])
IndexError: list index out of range
```

**Base** — 3/3 behavioral checks; cause 1/2, explanation 1/2.

`````text
```json
{
  "category": "IndexError",
  "root_cause": "The function `next_job` attempts to access an element at index 0 from an empty list, which results in an `IndexError`. This error occurs because attempting to access an element at an index that does not exist in the list is undefined behavior.",
  "corrected_code": "def next_job(jobs):\n    if jobs:\n        return jobs[0]\n    else:\n        return None",
  "explanation": "The original code incorrectly returns `None` when the input list `jobs` is empty, which is incorrect according to the problem statement. The corrected code checks if the list is empty before attempting to access its first element, ensuring that no `IndexError` is raised."
}
```
`````

**Adapter** — 0/3 behavioral checks; cause 1/2, explanation 0/2.

`````text
{"category": "IndexError", "root_cause": "The expression 'jobs[0]' accesses an element at that index when there is no such element.", "corrected_code": "def next_job(jobs):\n    if jobs:\n        return None\n    return jobs.pop(0)", "explanation": "Use 'jobs.pop(0)' to remove and return the first remaining element."}
`````

Failed inputs and expected values

```text
next_job([]) -> None
next_job(['sync']) -> 'sync'
next_job(['a', 'b']) -> 'a'
```

Review: Both identify the invalid access. A explains an empty check but reverses the original guard in its description. Pop still fails on an empty list.

## bucket-owners

The dictionary has no list for the first occurrence of each initial.

```python
def buckets(labels):
    groups = {}
    for label in labels:
        first = label[0]
        groups[first].append(label)
    return groups
```

```text
buckets(['ash', 'birch', 'ant'])
KeyError: 'a'
```

**Base** — 3/3 behavioral checks; cause 2/2, explanation 2/2.

`````text
```json
{
  "category": "KeyError",
  "root_cause": "The key 'a' does not exist in the dictionary `groups`.",
  "corrected_code": "def buckets(labels):\n    groups = {}\n    for label in labels:\n        first = label[0]\n        if first not in groups:\n            groups[first] = []\n        groups[first].append(label)\n    return groups",
  "explanation": "The original code attempted to append an element to a dictionary without checking if the key already exists. This can lead to a KeyError if the key is missing. The corrected code checks if the key exists before appending the element, ensuring that the operation is safe."
}
```
`````

**Adapter** — 1/3 behavioral checks; cause 0/2, explanation 0/2.

`````text
{"category": "KeyError", "root_cause": "The expression 'label[0]' selects the first character of each label where that character is missing from some labels.", "corrected_code": "def buckets(labels):\n    groups = {}\n    for label in labels:\n        first = label\n        groups[first].append(label)\n    return groups", "explanation": "Use 'first' at that operation to restore the intended selection."}
`````

Failed inputs and expected values

```text
buckets(['ash', 'birch', 'ant']) -> {'a': ['ash', 'ant'], 'b': ['birch']}
buckets(['bee']) -> {'b': ['bee']}
```

Review: A locates the missing dictionary entry and guards it. B incorrectly blames a missing character.

## text-parts

An unrestricted split produces more than two pieces when the value contains a colon.

```python
def split_header(line):
    name, value = line.split(':')
    return [name.strip(), value.strip()]
```

```text
split_header('Time: 10:30')
ValueError: too many values to unpack (expected 2)
```

**Base** — 3/3 behavioral checks; cause 2/2, explanation 2/2.

`````text
```json
{
  "category": "ValueError",
  "root_cause": "The `split` method returns a list of strings, but in this case, it returned more than two elements.",
  "corrected_code": "def split_header(line):\n    name, value = line.split(':', 1)\n    return [name.strip(), value.strip()]",
  "explanation": "The `split` method is designed to split a string into a list of substrings based on a specified delimiter. By default, it splits at each occurrence of the delimiter. However, if you specify a limit (`maxsplit` parameter), it will stop splitting after that many occurrences. In this case, we set `maxsplit=1`, which means the `split` method will only split the string once, resulting in a list containing two elements."
}
```
`````

**Adapter** — 0/3 behavioral checks; cause 0/2, explanation 0/2.

`````text
{"category": "ValueError", "root_cause": "The expression 'line.split(':')" splits at the first colon instead of the last.", "corrected_code": "def split_header(line):\n    name, value = line.rsplit(':', 1)\n    return [name.strip(), value.strip()]", "explanation": "Use 'line.rsplit(':', 1)' to restore the intended rightmost split."}
`````

Failed inputs and expected values

```text
split_header('Time: 10:30') -> ['Time', '10:30']
split_header('X: y') -> ['X', 'y']
split_header('Uri:a:b:c') -> ['Uri', 'a:b:c']
```

Review: A connects excess split pieces to maxsplit. B has no usable structured prose.

## ordered-scores

The in-place list sort returns None, which cannot be indexed.

```python
def leader(scores):
    ranked = scores.sort(reverse=True)
    return ranked[0]
```

```text
leader([2, 9, 1])
TypeError: 'NoneType' object is not subscriptable
```

**Base** — 3/3 behavioral checks; cause 1/2, explanation 0/2.

`````text
```json
{
  "category": "TypeError",
  "root_cause": "The `sort()` method returns `None` if no key is provided, which causes an error when trying to access the first element of the sorted list.",
  "corrected_code": "def leader(scores):\n    ranked = sorted(scores, reverse=True)\n    return ranked[0] if ranked else None",
  "explanation": "The original code attempts to sort the list and then return the first element. However, if the list is empty, `sorted()` returns `None`, causing a TypeError when trying to access the first element. The corrected code checks if `ranked` is `None` before attempting to access its elements, returning `None` in such cases."
}
```
`````

**Adapter** — 3/3 behavioral checks; cause 0/2, explanation 1/2.

`````text
{"category": "TypeError", "root_cause": "The sort operation returns None when it fails.", "corrected_code": "def leader(scores):\n    ranked = sorted(scores, reverse=True)\n    return ranked[0]", "explanation": "Use sorted to restore the intended sort."}
`````

Review: A recognizes None but gives it a false dependency on key and falsely describes sorted on empty input. B incorrectly treats None as a failure signal, although sorted is a useful replacement.

## half-open-span

Range excludes its stop so the requested final day is missing.

```python
def inclusive_days(start, end):
    return list(range(start, end))
```

```text
inclusive_days(3, 5)
AssertionError: expected [3, 4, 5], observed [3, 4]
```

**Base** — 3/3 behavioral checks; cause 2/2, explanation 2/2.

`````text
```json
{
  "category": "AssertionError",
  "root_cause": "The range function in Python does not include the stop value by default.",
  "corrected_code": "def inclusive_days(start, end):\n    return list(range(start, end + 1))",
  "explanation": "To ensure that the range includes both start and end values, we need to add 1 to the end parameter in the range function."
}
```
`````

**Adapter** — 3/3 behavioral checks; cause 2/2, explanation 2/2.

`````text
{"category": "WrongResult", "root_cause": "The range stops at its exclusive upper bound.", "corrected_code": "def inclusive_days(start, end):\n    return list(range(start, end + 1))", "explanation": "Use 'range(start, end + 1)' to include the final day."}
`````

Review: Both correctly identify the exclusive stop and explain adding one.

## rolling-mean

An empty list has length zero, making the denominator zero.

```python
def mean_or_zero(values):
    return sum(values) / len(values)
```

```text
mean_or_zero([])
ZeroDivisionError: division by zero
```

**Base** — 3/3 behavioral checks; cause 2/2, explanation 2/2.

`````text
```json
{
  "category": "ZeroDivisionError",
  "root_cause": "The function attempts to divide by zero when the input list is empty.",
  "corrected_code": "def mean_or_zero(values):\n    if not values:\n        return 0\n    return sum(values) / len(values)",
  "explanation": "To fix this error, we added a check at the beginning of the function to see if the input list `values` is empty. If it is, we return 0 instead of attempting to divide by zero. This prevents the ZeroDivisionError from occurring."
}
```
`````

**Adapter** — 3/3 behavioral checks; cause 1/2, explanation 1/2.

`````text
{"category": "ZeroDivisionError", "root_cause": "The expression 'len(values)' returns zero when empty.", "corrected_code": "def mean_or_zero(values):\n    return sum(values) / max(len(values), 1)", "explanation": "Use 'max(len(values), 1)' at that operation to restore the intended minimum."}
`````

Review: A links the zero denominator to the empty case. B identifies zero length and offers a working denominator bound without explaining the specified empty result.

## table-alias

List repetition copies references to the same inner row, so one write changes every row.

```python
def mark_cell(n, row, col):
    grid = [[0] * n] * n
    grid[row][col] = 1
    return grid
```

```text
mark_cell(2, 0, 1)
AssertionError: expected [[0, 1], [0, 0]], observed [[0, 1], [0, 1]]
```

**Base** — 3/3 behavioral checks; cause 2/2, explanation 2/2.

`````text
```json
{
  "category": "AssertionError",
  "root_cause": "The test case expects [[0, 1], [0, 0]] but got [[0, 1], [0, 1]]. This is because the grid is initialized to [[0] * n] * n, which creates a list of lists where each inner list is a reference to the same list. Therefore, when you modify one element in one inner list, it affects all other inner lists.",
  "corrected_code": "def mark_cell(n, row, col):\n    grid = [[0] * n for _ in range(n)]\n    grid[row][col] = 1\n    return grid",
  "explanation": "In the original code, `grid = [[0] * n] * n`, each inner list references the same list. When you modify an element in one inner list, it affects all other inner lists. To fix this, we use a list comprehension to create a new list of lists for each row."
}
```
`````

**Adapter** — 1/3 behavioral checks; cause 1/2, explanation 0/2.

`````text
{"category": "WrongResult", "root_cause": "The expression '[[0] * n] * n' creates a list of lists where each inner list shares its common element.", "corrected_code": "def mark_cell(n, row, col):\n    grid = [[0] * n] * n\n    grid[row][col] = 1\n    return grid", "explanation": "Use '[[0] * n] * 1' at that operation to create a fresh list for each nested list."}
`````

Failed inputs and expected values

```text
mark_cell(2, 0, 1) -> [[0, 1], [0, 0]]
mark_cell(2, 1, 0) -> [[0, 0], [1, 0]]
```

Review: A identifies repeated references to the same row. B gestures at sharing but multiplying by one produces only one row.

## consume-stream

The first sum exhausts the iterator and the second receives no items.

```python
def repeat_read(items):
    stream = iter(items)
    return [sum(stream), sum(stream)]
```

```text
repeat_read([1, 2])
AssertionError: expected [3, 3], observed [3, 0]
```

**Base** — 1/3 behavioral checks; cause 2/2, explanation 1/2.

`````text
```json
{
  "category": "AssertionError",
  "root_cause": "The second call to `stream` does not yield any more elements after the first call.",
  "corrected_code": "def repeat_read(items):\n    stream = iter(items)\n    return [sum(stream), sum(stream)]",
  "explanation": "The issue arises because the second call to `stream` is trying to read from an iterator that has already been exhausted by the first call. To fix this, we need to create a new iterator for each call to `sum()`. This can be achieved by calling `iter()` again on the same iterable."
}
```
`````

Failed inputs and expected values

```text
repeat_read([1, 2]) -> [3, 3]
repeat_read([-1, 4]) -> [3, 3]
```

**Adapter** — 0/3 behavioral checks; cause 0/2, explanation 0/2.

`````text
{"category": "WrongResult", "root_cause": "The expression 'sum(stream)' adds the last value instead of averaging it.", "corrected_code": "def repeat_read(items):\n    stream = iter(items)\n    return [sum(itertools.accumulate(stream)), sum(itertools.accumulate(stream))]", "explanation": "Use 'itertools.accumulate(stream)' at each call to restore the intended average."}
`````

Failed inputs and expected values

```text
repeat_read([1, 2]) -> [3, 3]
repeat_read([]) -> [0, 0]
repeat_read([-1, 4]) -> [3, 3]
```

Review: A identifies exhaustion; iterating the original list twice works for reusable inputs, but iter() cannot rewind an iterator. B invents an averaging operation.

## field-number

The ticket number is stored as text and cannot be added to an integer.

```python
def next_ticket(record):
    return record['number'] + 1
```

```text
next_ticket({'number': '009'})
TypeError: can only concatenate str (not "int") to str
```

**Base** — 3/3 behavioral checks; cause 2/2, explanation 2/2.

`````text
```json
{
  "category": "TypeError",
  "root_cause": "The operation `+` is used between an integer and a string in Python, which results in a TypeError.",
  "corrected_code": "def next_ticket(record):\n    return int(record['number']) + 1",
  "explanation": "To fix this error, we need to convert the string value of the 'number' key to an integer before performing the addition. This is done by adding `int(record['number'])` before the `+ 1`. The corrected code ensures that both operands are of the same type, thus avoiding the TypeError."
}
```
`````

**Adapter** — 3/3 behavioral checks; cause 0/2, explanation 1/2.

`````text
{"category": "TypeError", "root_cause": "The expression 'record['number']' adds two strings.", "corrected_code": "def next_ticket(record):\n    return int(record['number']) + 1", "explanation": "Use 'int(record['number'])' at that operation."}
`````

Review: A describes the string/integer mismatch and the conversion. B says two strings are added and offers a useful cast with no rationale.

## predicate-call

The code tests a bound method object, which is truthy even for whitespace.

```python
def nonblank(text):
    return bool(text.strip)
```

```text
nonblank('   ')
AssertionError: expected False, observed True
```

**Base** — 3/3 behavioral checks; cause 0/2, explanation 1/2.

`````text
```json
{
  "category": "AssertionError",
  "root_cause": "The `strip()` method removes leading and trailing whitespace from the string, but it does not remove any internal whitespace. Therefore, if the input string contains only spaces, `strip()` will return an empty string, which is considered truthy in Python.",
  "corrected_code": "def nonblank(text):\n    return bool(text.strip() != '')",
  "explanation": "To fix this issue, we need to check if the stripped version of the string is not an empty string. This can be done by comparing the result of `strip()` with an empty string (`''`). If they are not equal, then the original string was not blank, and the function should return `True`. Otherwise, it should return `False`. "
}
```
`````

**Adapter** — 3/3 behavioral checks; cause 0/2, explanation 0/2.

`````text
{"category": "WrongResult", "root_cause": "The strip method removes leading and trailing spaces but leaves in the middle.", "corrected_code": "def nonblank(text):\n    return bool(text.lstrip() + text.rstrip())", "explanation": "Use lstrip to restore the missing space."}
`````

Review: A falsely calls the empty string truthy. Its explicit comparison after invoking strip is workable, but it misses the uncalled method. B's lstrip suggestion misses the mechanism.

## seat-code

Subtracting the first letter produces a zero-based offset, one below the seat number.

```python
def seat(code):
    """Map the letters A through Z to seat numbers 1 through 26."""
    return ord(code) - ord('A')
```

```text
seat('A')
AssertionError: expected 1, observed 0
```

**Base** — 3/3 behavioral checks; cause 0/2, explanation 1/2.

`````text
```json
{
  "category": "ValueError",
  "root_cause": "The `ord()` function returns an integer representing the Unicode character.",
  "corrected_code": "def seat(code):\n    \"\"\"Map the letters A through Z to seat numbers 1 through 26.\"\"\"\n    return ord(code) - ord('A') + 1",
  "explanation": "The original code subtracts the ASCII value of 'A' from the ASCII value of the input letter, which gives the seat number. However, the `ord()` function returns an integer representing the Unicode character, so we need to add 1 to get the correct seat number."
}
```
`````

**Adapter** — 0/3 behavioral checks; cause 0/2, explanation 0/2.

`````text
{"category": "WrongResult", "root_cause": "The expression 'ord(code) - ord('A')" subtracts instead of adds.", "corrected_code": "def seat(code):\n    \"\"\"Map the letters A through Z to seat numbers 1 through 26.\"\"\"\n    return ord(code) + ord('A')", "explanation": "Use 'ord(code) + ord('A')" at that operation."}
`````

Failed inputs and expected values

```text
seat('A') -> 1
seat('K') -> 11
seat('Z') -> 26
```

Review: A describes ord without identifying the zero-based origin; it proposes adding one but attributes that to the Unicode result type. B is unparseable.

## invoice-label

The numeric serial is concatenated directly with a string.

```python
def invoice(serial):
    """Render an integer serial as an INV- identifier."""
    return 'INV-' + serial
```

```text
invoice(8)
TypeError: can only concatenate str (not "int") to str
```

**Base** — 3/3 behavioral checks; cause 0/2, explanation 2/2.

`````text
```json
{
  "category": "TypeError",
  "root_cause": "The TypeError occurs because the `serial` parameter is expected to be an integer, but it is being passed as a string.",
  "corrected_code": "def invoice(serial):\n    \"\"\"Render an integer serial as an INV- identifier.\"\"\"\n    return 'INV-' + str(serial)",
  "explanation": "To fix this error, we need to convert the `serial` parameter from an integer to a string before concatenating it with 'INV-'. This is done by adding `str(serial)` inside the `return` statement."
}
```
`````

**Adapter** — 3/3 behavioral checks; cause 0/2, explanation 1/2.

`````text
{"category": "TypeError", "root_cause": "The expression 'serial' is converted to an integer before concatenation.", "corrected_code": "def invoice(serial):\n    \"\"\"Render an integer serial as an INV- identifier.\"\"\"\n    return 'INV-' + str(serial)", "explanation": "Use 'str(serial)' at that operation to restore the original string."}
`````

Review: Neither cause matches the given integer input. A names a useful cast. B's rationale correctly explains casting the integer before concatenation.

## optional-alias

Testing the value indexes a potentially absent key and also rejects valid falsey aliases.

```python
def alias(record):
    """Use alias when it exists, including an empty alias, otherwise use name."""
    if record['alias']:
        return record['alias']
    return record['name']
```

```text
alias({'name':'Ada'})
KeyError: 'alias'
```

**Base** — 0/3 behavioral checks; cause 0/2, explanation 0/2.

`````text
```json
{
  "category": "KeyError",
  "root_cause": "The function `alias` is trying to access the key `'alias'` in the dictionary `record`, but this key does not exist.",
  "corrected_code": "def alias(record):\n    \"\"\"Use alias when it exists, including an empty alias, otherwise use name.\"\"\"\n    if 'alias' in record:\n        return record['alias']\n    return record['name']",
  "explanation": "To fix the error, we need to check if the key `'alias'` exists in the dictionary `record` before attempting to access it. This can be done using the `in` keyword. If the key exists, we return its value; otherwise, we return the value of the key `'name'`. This ensures that the function behaves correctly even if the input dictionary does not contain the key `'alias'"."
}
```
`````

Failed inputs and expected values

```text
alias({'name':'Ada'}) -> 'Ada'
alias({'name':'A','alias':''}) -> ''
alias({'alias':'bb'}) -> 'bb'
```

**Adapter** — 3/3 behavioral checks; cause 2/2, explanation 0/2.

`````text
{"category": "KeyError", "root_cause": "The expression 'record['alias']' accesses the missing key.", "corrected_code": "def alias(record):\n    \"\"\"Use alias when it exists, including an empty alias, otherwise use name.\"\"\"\n    if 'alias' in record:\n        return record['alias']\n    return record['name']", "explanation": "'in record' includes missing keys."}
`````

Review: B identifies the absent-key lookup; membership checking does not include missing keys as its rationale claims.

## suffix-check

The attribute lower is a bound method and has no string endswith operation.

```python
def is_backup(filename):
    """Identify names ending in .bak without regard to case."""
    return filename.lower.endswith('.bak')
```

```text
is_backup('SAVE.BAK')
AttributeError: 'builtin_function_or_method' object has no attribute 'endswith'
```

**Base** — 3/3 behavioral checks; cause 2/2, explanation 2/2.

`````text
```json
{
  "category": "AttributeError",
  "root_cause": "The `endswith` method is not available on built-in functions like `filename.lower`. It should be called on strings.",
  "corrected_code": "def is_backup(filename):\n    \"\"\"Identify names ending in .bak without regard to case.\"\"\"\n    return filename.lower().endswith('.bak')",
  "explanation": "To fix this error, we need to call the `endswith` method on the result of `lower()`, which converts the entire string to lowercase before checking if it ends with `.bak`. This ensures that the comparison is case-insensitive."
}
```
`````

**Adapter** — 0/3 behavioral checks; cause 0/2, explanation 0/2.

`````text
{"category": "AttributeError", "root_cause": "The expression 'filename.lower.endswith('.bak')" uses the method where an attribute is required.", "corrected_code": "def is_backup(filename):\n    \"\"\"Identify names ending in .bak without regard to case.\"\"\"\n    return filename.lower().endswith('.bak')", "explanation": "Use 'filename.lower().endswith('.bak')" at that operation to restore the intended attribute."}
`````

Failed inputs and expected values

```text
is_backup('SAVE.BAK') -> True
is_backup('bak.txt') -> False
is_backup('a.bak.tmp') -> False
```

Review: B distinguishes the lower method object from its string return value and explains the call sequence.

## last-neighbor

A matching final word has no following index.

```python
def after_token(words, token):
    """Return the word after the first matching token, or None."""
    for i, word in enumerate(words):
        if word == token:
            return words[i + 1]
    return None
```

```text
after_token(['x'], 'x')
IndexError: list index out of range
```

**Base** — 3/3 behavioral checks; cause 1/2, explanation 2/2.

`````text
```json
{
  "category": "ValueError",
  "root_cause": "The loop condition `i < len(words)` is incorrect because it will fail when `i` equals `len(words) - 1`, which is the last index of the list.",
  "corrected_code": "def after_token(words, token):\n    \"\"\"Return the word after the first matching token, or None.\"\"\"\n    for i, word in enumerate(words):\n        if word == token:\n            return words[i + 1] if i + 1 < len(words) else None\n    return None",
  "explanation": "The original code attempts to access `words[i + 1]` when `i` equals `len(words) - 1`, which would result in an `IndexError`. The corrected code checks if `i + 1` is less than the length of the list before accessing the next element."
}
```
`````

**Adapter** — 3/3 behavioral checks; cause 0/2, explanation 1/2.

`````text
{"category": "IndexError", "root_cause": "The expression 'i + 1' adds the right operand before testing the sum.", "corrected_code": "def after_token(words, token):\n    \"\"\"Return the word after the first matching token, or None.\"\"\"\n    for i, word in enumerate(words):\n        if word == token:\n            return words[i + 1] if i + 1 < len(words) else None\n    return None", "explanation": "Use 'i + 1 if i + 1 < len(words) else None' at that operation."}
`````

Review: A invents an existing guard but accurately explains the final lookahead and its bound. B suggests a bound without correctly diagnosing it.

## parse-rate

The handler catches a dictionary lookup failure while int raises ValueError on malformed text.

```python
def read_rate(text):
    """Return the integer or None for malformed numeric text."""
    try:
        return int(text)
    except KeyError:
        return None
```

```text
read_rate('bad')
ValueError: invalid literal for int() with base 10: 'bad'
```

**Base** — 3/3 behavioral checks; cause 1/2, explanation 2/2.

`````text
```json
{
  "category": "ValueError",
  "root_cause": "The `int()` function cannot convert non-numeric strings to integers.",
  "corrected_code": "def read_rate(text):\n    \"\"\"Return the integer or None for malformed numeric text.\"\"\"\n    try:\n        return int(text)\n    except ValueError:\n        return None",
  "explanation": "The original code attempted to convert a string that is not a valid number to an integer using the `int()` function. This operation raises a `ValueError` if the string does not represent a valid integer. The corrected code includes a try-except block that catches this error and returns `None` instead of raising an exception."
}
```
`````

**Adapter** — 3/3 behavioral checks; cause 0/2, explanation 1/2.

`````text
{"category": "ValueError", "root_cause": "The expression 'keyError' is an unbound name.", "corrected_code": "def read_rate(text):\n    \"\"\"Return the integer or None for malformed numeric text.\"\"\"\n    try:\n        return int(text)\n    except ValueError:\n        return None", "explanation": "Use 'ValueError' at that operation."}
`````

Review: A identifies conversion failure and explains catching ValueError. B invents an unbound name but names the right replacement handler.

## call-notes

The default list is created once at function definition, so calls without a history share it.

```python
def note(value, history=[]):
    """Append to the supplied history. Omitted histories must be fresh per call."""
    history.append(value)
    return history
```

```text
(list(note(1)),list(note(2)))
AssertionError: expected ([1], [2]), observed ([1], [1, 2])
```

**Base** — 3/3 behavioral checks; cause 1/2, explanation 2/2.

`````text
```json
{
  "category": "AssertionError",
  "root_cause": "The `history` list is being modified in-place within the function, which can lead to unexpected behavior when assertions are made.",
  "corrected_code": "def note(value, history=None):\n    \"\"\"Append to the supplied history. Omitted histories must be fresh per call.\"\"\"\n    if history is None:\n        history = []\n    history.append(value)\n    return history",
  "explanation": "The original code modifies the `history` list directly within the function, which can cause issues when assertions are made. The corrected code checks if `history` is `None`, and if so, initializes it as an empty list before appending the value. This ensures that each call to `note` starts with a fresh list."
}
```
`````

**Adapter** — 1/3 behavioral checks; cause 0/2, explanation 0/2.

`````text
{"category": "WrongResult", "root_cause": "The expression 'history.append(value)' appends instead of prepending.", "corrected_code": "def note(value, history=[]):\n    \"\"\"Append to the supplied history. Omitted histories must be fresh per call.\"\"\"\n    history.insert(0,value)\n    return history", "explanation": "Use 'history.insert(0,value)' at that operation."}
`````

Failed inputs and expected values

```text
(list(note(1)),list(note(2))) -> ([1],[2])
note(4,[3]) -> [3,4]
```

Review: B notices mutation but omits definition-time allocation in the cause. Its sentinel explanation correctly allocates a new list on omitted calls. Insertion order is irrelevant.

## range-band

The disjunction accepts values meeting only one side of the interval.

```python
def in_band(v, low, high):
    """Include the low endpoint and exclude the high endpoint."""
    return low <= v or v < high
```

```text
in_band(100,2,5)
AssertionError: expected False, observed True
```

**Base** — 4/4 behavioral checks; cause 1/2, explanation 0/2.

`````text
```json
{
  "category": "AssertionError",
  "root_cause": "The condition `low <= v or v < high` is incorrect because it includes both endpoints of the range.",
  "corrected_code": "def in_band(v, low, high):\n    \"\"\"Include the low endpoint and exclude the high endpoint.\"\"\"\n    return low <= v < high",
  "explanation": "The original code incorrectly checks if `v` is less than or equal to `low` or greater than `high`. This means that `v` can be equal to either `low` or `high`, which is not what we want when including the low endpoint but excluding the high endpoint."
}
```
`````

**Adapter** — 1/4 behavioral checks; cause 0/2, explanation 0/2.

`````text
{"category": "WrongResult", "root_cause": "The expression 'low <= v' includes the lower bound where it should be excluded.", "corrected_code": "def in_band(v, low, high):\n    \"\"\"Include the low endpoint and exclude the high endpoint.\"\"\"\n    return low < v or v < high", "explanation": "Use 'low < v' at that operation to restore the intended inequality."}
`````

Failed inputs and expected values

```text
in_band(100,2,5) -> False
in_band(5,2,5) -> False
in_band(-1,2,5) -> False
```

Review: A would exclude the valid low endpoint. B points to the actual expression and an unwanted accepted endpoint but reverses comparisons and misses why disjunction admits out-of-range values.

## comments

Partition's last component contains the trailing comment, not the prefix.

```python
def uncomment(line):
    """Drop text from the first hash onward, preserving preceding spaces."""
    return line.partition('#')[2]
```

```text
uncomment('x # y')
AssertionError: expected 'x ', observed ' y'
```

**Base** — 1/3 behavioral checks; cause 1/2, explanation 0/2.

`````text
```json
{
  "category": "ValueError",
  "root_cause": "The `partition` method returns a tuple where the first element is before the delimiter, the second is the delimiter itself, and the third is after the delimiter. In this case, the delimiter is '#', so the first element is 'x ', which is not what we want.",
  "corrected_code": "def uncomment(line):\n    \"\"\"Drop text from the first hash onward, preserving preceding spaces.\"\"\"\n    return line.lstrip('#').lstrip()",
  "explanation": "To fix the issue, we can use the `lstrip` method twice to remove both leading '#' characters and any additional leading whitespace that might be present in the input string."
}
```
`````

Failed inputs and expected values

```text
uncomment('x # y') -> 'x '
uncomment('# todo') -> ''
```

**Adapter** — 3/3 behavioral checks; cause 0/2, explanation 1/2.

`````text
{"category": "WrongResult", "root_cause": "The expression 'partition('#)[2]' splits at the literal '#' instead of the first occurrence.", "corrected_code": "def uncomment(line):\n    \"\"\"Drop text from the first hash onward, preserving preceding spaces.\"\"\"\n    return line.split('#', 1)[0]", "explanation": "Use 'split('#', 1)[0]' to join before the first occurrence."}
`````

Review: A describes partition's tuple but rejects the required prefix and proposes stripping whitespace. B gives a workable split expression but misstates partition and calls selection joining.

## nested-config

The outer dictionary lookup can raise before the inner default is reached.

```python
def port(cfg):
    """Return the nested service port, defaulting to 80 for missing fields."""
    return cfg['service'].get('port', 80)
```

```text
port({})
KeyError: 'service'
```

**Base** — 3/3 behavioral checks; cause 2/2, explanation 2/2.

`````text
```json
{
  "category": "KeyError",
  "root_cause": "The function `port` is trying to access a key named 'service' in the dictionary `cfg`, but this key does not exist.",
  "corrected_code": "def port(cfg):\n    \"\"\"Return the nested service port, defaulting to 80 for missing fields.\"\"\"\n    return cfg.get('service', {}).get('port', 80)",
  "explanation": "To fix the error, we need to ensure that the key 'service' exists in the dictionary `cfg`. We can do this by adding a check using the `get` method with two arguments: the key to look for and a default value. In this case, we want to get the value of 'service' and if it doesn't exist, we want to return an empty dictionary. Then, we can safely access the 'port' key within this dictionary."
}
```
`````

**Adapter** — 3/3 behavioral checks; cause 2/2, explanation 1/2.

`````text
{"category": "KeyError", "root_cause": "The expression 'cfg['service']' accesses the key without checking its presence.", "corrected_code": "def port(cfg):\n    \"\"\"Return the nested service port, defaulting to 80 for missing fields.\"\"\"\n    return cfg.get('service', {}).get('port', 80)", "explanation": "Use 'cfg.get('service', {})'.get('port', 80)' at that operation."}
`````

Review: Both identify the unguarded outer key. A offers the defaulting expression without explaining why it works. B connects the empty mapping default to safe second-level lookup.

## trim-extension

Partitioning from the left drops everything after the first dot.

```python
def stem(path):
    """Remove the final extension, retaining dots earlier in the filename."""
    head, sep, tail = path.partition('.')
    return head if sep else path
```

```text
stem('a.b.txt')
AssertionError: expected 'a.b', observed 'a'
```

**Base** — 3/3 behavioral checks; cause 1/2, explanation 2/2.

`````text
```json
{
  "category": "ValueError",
  "root_cause": "The `partition` method returns three parts of the string: the part before the first dot (`head`), the separator (`sep`), and the part after the last dot (`tail`). If there is no dot in the string, `sep` will be an empty string, and `tail` will be the entire string. In this case, since there is no dot, `sep` is an empty string, and `tail` is 'a'. The function then attempts to return `head`, which is 'a', but it should have returned 'a.b' instead.",
  "corrected_code": "def stem(path):\n    \"\"\"Remove the final extension, retaining dots earlier in the filename.\"\"\"\n    head, sep, tail = path.rpartition('.')\n    return head if sep else path",
  "explanation": "The `rpartition` method returns three parts of the string: the part before the last dot (`head`), the separator (`sep`), and the part after the last dot (`tail`). This method is more appropriate for strings that may contain multiple dots, as it allows you to specify the position from which to partition the string. By using `rpartition('.')`, we ensure that the function correctly handles cases where there are multiple dots in the filename."
}
```
`````

**Adapter** — 2/3 behavioral checks; cause 0/2, explanation 0/2.

`````text
{"category": "WrongResult", "root_cause": "The expression 'sep' selects the separator instead of the expression 'path.partition('.')[1]' at that position.", "corrected_code": "def stem(path):\n    \"\"\"Remove the final extension, retaining dots earlier in the filename.\"\"\"\n    head, _, tail = path.partition('.')\n    return head if _ else path", "explanation": "Use '_' at that operation to restore the intended selection."}
`````

Failed inputs and expected values

```text
stem('a.b.txt') -> 'a.b'
```

Review: A notices the first-dot head but misdescribes the tail and absent-dot behavior. Its rightmost partition rationale addresses multiple dots. B changes the variable name.

## parallel-lists

The larger length lets the loop index past the shorter list.

```python
def match_pairs(a, b):
    """Pair items at matching positions, stopping at the shorter input."""
    return [(a[i], b[i]) for i in range(max(len(a), len(b)))]
```

```text
match_pairs([1],[2,3])
IndexError: list index out of range
```

**Base** — 3/3 behavioral checks; cause 2/2, explanation 2/2.

`````text
```json
{
  "category": "IndexError",
  "root_cause": "The loop iterates over indices up to the length of the longer list, but if the lists are of different lengths, it will try to access an index that does not exist in the shorter list.",
  "corrected_code": "def match_pairs(a, b):\n    \"\"\"Pair items at matching positions, stopping at the shorter input.\"\"\"\n    return [(a[i], b[i]) for i in range(min(len(a), len(b)))]",
  "explanation": "The corrected code uses `min` instead of `max` to determine the number of iterations, ensuring that the loop only accesses valid indices in both lists."
}
```
`````

**Adapter** — 3/3 behavioral checks; cause 0/2, explanation 1/2.

`````text
{"category": "IndexError", "root_cause": "The expression 'range(max(len(a), len(b)))' includes an upper bound that excludes the last valid index.", "corrected_code": "def match_pairs(a, b):\n    \"\"\"Pair items at matching positions, stopping at the shorter input.\"\"\"\n    return [(a[i], b[i]) for i in range(min(len(a), len(b)))]", "explanation": "Use 'range(min(len(a), len(b)))' at that operation to restore the intended upper bound."}
`````

Review: A explains why the shorter input determines the bound. B reverses the error direction but proposes the correct minimum.

## set-growth

The result is a set and does not implement list append.

```python
def register(tags, tag):
    """Return a set containing the old tags and the new tag."""
    result = set(tags)
    result.append(tag)
    return result
```

```text
register(['a'],'b')
AttributeError: 'set' object has no attribute 'append'
```

**Base** — 3/3 behavioral checks; cause 2/2, explanation 2/2.

`````text
```json
{
  "category": "AttributeError",
  "root_cause": "The `set` object does not have an `append` method.",
  "corrected_code": "def register(tags, tag):\n    \"\"\"Return a set containing the old tags and the new tag.\"\"\"\n    result = set(tags)\n    result.add(tag)  # Use add instead of append\n    return result",
  "explanation": "The `set` object in Python is designed to store unique elements. The `add` method is used to insert an element into a set, which automatically removes any duplicates. The `append` method, on the other hand, is used to add an element to a list, which can lead to duplicate entries if the same element is added multiple times."
}
```
`````

**Adapter** — 3/3 behavioral checks; cause 2/2, explanation 2/2.

`````text
{"category": "AttributeError", "root_cause": "The append method is missing from sets.", "corrected_code": "def register(tags, tag):\n    \"\"\"Return a set containing the old tags and the new tag.\"\"\"\n    result = set(tags)\n    result.add(tag)\n    return result", "explanation": "Use add to insert elements into sets."}
`````

Review: Both distinguish set insertion from list append and recommend add.

## sign-column

Adding the two booleans maps either nonzero sign to positive one.

```python
def signs(nums):
    """Map each integer to -1, 0 or 1."""
    return [(x > 0) + (x < 0) for x in nums]
```

```text
signs([-8,0,5])
AssertionError: expected [-1, 0, 1], observed [1, 0, 1]
```

**Base** — 3/3 behavioral checks; cause 0/2, explanation 0/2.

`````text
```json
{
  "category": "AssertionError",
  "root_cause": "The condition `(x > 0) + (x < 0)` is always true because `x` can only be either positive or negative.",
  "corrected_code": "def signs(nums):\n    \"\"\"Map each integer to -1, 0 or 1.\"\"\"\n    return [(x >= 0) - (x <= 0) for x in nums]",
  "explanation": "The original code incorrectly adds 1 if `x` is positive and subtracts 1 if `x` is negative. However, since `x` can only be either positive or negative, adding 1 and then subtracting 1 will always result in 0. The correct approach is to use the bitwise XOR operator (`^`) which returns 1 if the bits are different and 0 if they are the same. This way, we correctly map positive numbers to 1, negative numbers to -1, and zero to 0."
}
```
`````

**Adapter** — 1/3 behavioral checks; cause 0/2, explanation 0/2.

`````text
{"category": "WrongResult", "root_cause": "The expression 'x > 0' is true where it should be false.", "corrected_code": "def signs(nums):\n    \"\"\"Map each integer to -1, 0 or 1.\"\"\"\n    return [(x >= 0) + (x <= 0) for x in nums]", "explanation": "Use 'x >= 0' at that operation to restore the intended inequality."}
`````

Failed inputs and expected values

```text
signs([-8,0,5]) -> [-1,0,1]
signs([-1,-2]) -> [-1,-1]
```

Review: A ignores zero and incorrectly claims XOR can produce the intended negative sign. B changes a comparison without addressing the addition.

## row-decode

A bytes object expects a byte separator, while the contract asks for decoded string fields.

```python
def decode_row(blob):
    """Decode UTF-8 bytes and split tab-separated fields."""
    return blob.split('\t')
```

```text
decode_row(b'a\tb')
TypeError: a bytes-like object is required, not 'str'
```

**Base** — 3/3 behavioral checks; cause 1/2, explanation 0/2.

`````text
```json
{
  "category": "TypeError",
  "root_cause": "The `split` method expects a bytes-like object, but the input is a string.",
  "corrected_code": "def decode_row(blob):\n    \"\"\"Decode UTF-8 bytes and split tab-separated fields.\"\"\"\n    return blob.decode('utf-8').split('\\t')",
  "explanation": "To fix this error, we need to convert the string `blob` into a bytes-like object before calling the `split` method. We do this by using the `decode` method with the argument `'utf-8'`, which converts the string to bytes using UTF-8 encoding."
}
```
`````

**Adapter** — 3/3 behavioral checks; cause 1/2, explanation 0/2.

`````text
{"category": "TypeError", "root_cause": "The input must be a bytes-like object but received a string.", "corrected_code": "def decode_row(blob):\n    \"\"\"Decode UTF-8 bytes and split tab-separated fields.\"\"\"\n    return blob.decode('utf-8').split('\\t')", "explanation": "Use .decode('utf-8') to convert the string before splitting."}
`````

Review: Both gesture at a bytes/text mismatch without identifying the text separator used on bytes. Both misdescribe which type decode accepts or returns.

## veto-finally

Continue in finally overrides even a successful pending return.

```python
def first_int(items):
    """Return the first parseable integer or None."""
    for item in items:
        try:
            return int(item)
        finally:
            continue
    return None
```

```text
first_int(['x','2','3'])
AssertionError: expected 2, observed None
```

**Base** — 3/3 behavioral checks; cause 1/2, explanation 0/2.

`````text
```json
{
  "category": "ValueError",
  "root_cause": "The `finally` block is executed after the `return` statement, which means that if an exception occurs before the `return` statement, it will be caught by the `except` block but the `finally` block will still execute.",
  "corrected_code": "def first_int(items):\n    \"\"\"Return the first parseable integer or None.\"\"\"\n    for item in items:\n        try:\n            return int(item)\n        except ValueError:\n            continue\n    return None",
  "explanation": "The `finally` block was causing the function to return `None` even when an exception occurred before the `return` statement. By moving the `continue` statement inside the `try` block, we ensure that the function continues to iterate over the remaining items without returning prematurely."
}
```
`````

**Adapter** — 3/3 behavioral checks; cause 1/2, explanation 1/2.

`````text
{"category": "WrongResult", "root_cause": "The 'finally' clause skips the 'return' at that point.", "corrected_code": "def first_int(items):\n    \"\"\"Return the first parseable integer or None.\"\"\"\n    for item in items:\n        try:\n            return int(item)\n        except ValueError:\n            continue\n    return None", "explanation": "Use 'except ValueError' to handle invalid inputs."}
`````

Review: A notices finally but invents an existing except block and proposes moving continue into try. B locates the overridden return and names a suitable handler but omits the overriding continue mechanism.

## width-padding

The shortfall subtraction is reversed, so short strings receive no padding.

```python
def pad_right(text, width):
    """Pad with periods up to width, leaving longer strings intact."""
    return text + '.' * max(0, len(text) - width)
```

```text
pad_right('a',3)
AssertionError: expected 'a..', observed 'a'
```

**Base** — 1/3 behavioral checks; cause 0/2, explanation 0/2.

`````text
```json
{
  "category": "AssertionError",
  "root_cause": "The length of the input string is less than the specified width.",
  "corrected_code": "def pad_right(text, width):\n    \"\"\"Pad with periods up to width, leaving longer strings intact.\"\"\"\n    return text + '.' * max(0, width)",
  "explanation": "The original code was attempting to pad a string with periods until it reached a certain width. However, if the string's length is already greater than or equal to the specified width, no padding would be added. This resulted in an AssertionError when trying to pad a string that was shorter than the required width."
}
```
`````

Failed inputs and expected values

```text
pad_right('a',3) -> 'a..'
pad_right('long',2) -> 'long'
```

**Adapter** — 1/3 behavioral checks; cause 0/2, explanation 0/2.

`````text
{"category": "WrongResult", "root_cause": "The expression 'len(text) - width' subtracts the right operand instead of adding it.", "corrected_code": "def pad_right(text, width):\n    \"\"\"Pad with periods up to width, leaving longer strings intact.\"\"\"\n    return text + '.' * min(0, len(text) - width)", "explanation": "Use 'min(0, len(text) - width)' at that operation to restore the intended addition."}
`````

Failed inputs and expected values

```text
pad_right('a',3) -> 'a..'
pad_right('',1) -> '.'
```

Review: Neither identifies the reversed subtraction. A describes the expected short-input condition; B proposes a different clamp and addition.

## index-or-zero

Zero is a valid index but fails a truth-value test.

```python
def locate(seq, target):
    """Return the first index or -1, including a match at index zero."""
    index = next((i for i,x in enumerate(seq) if x == target), None)
    return index if index else -1
```

```text
locate(['a'],'a')
AssertionError: expected 0, observed -1
```

**Base** — 3/3 behavioral checks; cause 0/2, explanation 1/2.

`````text
```json
{
  "category": "AssertionError",
  "root_cause": "The `enumerate` function returns an iterator that produces tuples containing the index and value of each element in the sequence.",
  "corrected_code": "def locate(seq, target):\n    \"\"\"Return the first index or -1, including a match at index zero.\"\"\"\n    index = next((i for i,x in enumerate(seq) if x == target), None)\n    return index if index is not None else -1",
  "explanation": "The original code uses `next((i for i,x in enumerate(seq) if x == target), None)` which returns `None` when no match is found. However, the `assert` statement expects an integer result. To fix this, we check if `index` is `None` before returning it. If `index` is `None`, we return `-1`. This ensures that the `assert` statement passes without raising an error."
}
```
`````

**Adapter** — 3/3 behavioral checks; cause 0/2, explanation 0/2.

`````text
{"category": "WrongResult", "root_cause": "The expression 'x == target' compares the right operand before the left.", "corrected_code": "def locate(seq, target):\n    \"\"\"Return the first index or -1, including a match at index zero.\"\"\"\n    index = next((i for i,x in enumerate(seq) if x == target), None)\n    return index if index is not None else -1", "explanation": "Use 'x == target' at that operation to restore the intended comparison."}
`````

Review: A leaves the comparison unchanged. B describes enumerate rather than zero's false truth value but proposes the appropriate None check.

## step-chunks

The stop bound permits only starts with a full chunk and discards the remainder.

```python
def blocks(text, n):
    """Return chunks of n characters, retaining a final short chunk; n is positive."""
    return [text[i:i+n] for i in range(0, len(text)-n+1, n)]
```

```text
blocks('abcde',2)
AssertionError: expected ['ab', 'cd', 'e'], observed ['ab', 'cd']
```

**Base** — 1/3 behavioral checks; cause 1/2, explanation 0/2.

`````text
```json
{
  "category": "AssertionError",
  "root_cause": "The length of the last chunk is less than n.",
  "corrected_code": "def blocks(text, n):\n    \"\"\"Return chunks of n characters, retaining a final short chunk; n is positive.\"\"\"\n    if len(text) % n != 0:\n        text += '_'\n    return [text[i:i+n] for i in range(0, len(text)-n+1, n)]",
  "explanation": "To fix this issue, we need to ensure that the last chunk has at least n characters. If the length of the input text is not divisible by n, we append an underscore ('_') to the end of the text before splitting it into chunks. This way, the last chunk will always have at least n characters."
}
```
`````

Failed inputs and expected values

```text
blocks('abcde',2) -> ['ab','cd','e']
blocks('x',4) -> ['x']
```

**Adapter** — 3/3 behavioral checks; cause 2/2, explanation 1/2.

`````text
{"category": "WrongResult", "root_cause": "The expression 'len(text)-n+1' excludes the last slice.", "corrected_code": "def blocks(text, n):\n    \"\"\"Return chunks of n characters, retaining a final short chunk; n is positive.\"\"\"\n    return [text[i:i+n] for i in range(0, len(text), n)]", "explanation": "Use 'len(text)' at that operation to restore the intended length."}
`````

Review: A notices the partial chunk but suggests padding it, contrary to the contract. B locates the restrictive stop and restores the length, with little explanation of the retained remainder.

## call-count

The dictionary default persists between calls, and the None guard cannot replace it.

```python
def tally(keys, counts={}):
    """Count keys in a fresh mapping unless the caller supplies one."""
    if counts is None:
        counts = {}
    for key in keys:
        counts[key] = counts.get(key, 0) + 1
    return counts
```

```text
(dict(tally('a')),dict(tally('b')))
AssertionError: expected ({'a': 1}, {'b': 1}), observed ({'a': 1}, {'a': 1, 'b': 1})
```

**Base** — 3/3 behavioral checks; cause 1/2, explanation 1/2.

`````text
```json
{
  "category": "AssertionError",
  "root_cause": "The dictionary returned by `tally` should be a new instance of `counts`, but it's being modified in place.",
  "corrected_code": "def tally(keys, counts=None):\n    \"\"\"Count keys in a fresh mapping unless the caller supplies one.\"\"\"\n    if counts is None:\n        counts = {}\n    for key in keys:\n        counts[key] = counts.get(key, 0) + 1\n    return dict(counts)",
  "explanation": "In the original code, `counts` is passed by reference to the function, so any modifications made inside the function affect the original variable. To avoid this, we create a new dictionary `counts` before modifying it."
}
```
`````

**Adapter** — 3/3 behavioral checks; cause 0/2, explanation 0/2.

`````text
{"category": "WrongResult", "root_cause": "The expression 'counts is None' evaluates true when the operand is an empty dictionary.", "corrected_code": "def tally(keys, counts=None):\n    \"\"\"Count keys in a fresh mapping unless the caller supplies one.\"\"\"\n    if counts is None:\n        counts = {}\n    for key in keys:\n        counts[key] = counts.get(key, 0) + 1\n    return counts", "explanation": "Use 'counts is None' at that operation to restore the intended condition."}
`````

Review: A notices shared mutation but does not isolate the definition-time default or preserve the caller's explicit dictionary in its reasoning. B wrongly equates an empty dictionary with None.

## pair-swap

Sequential assignment overwrites the old first value before it can move to the second slot.

```python
def exchange(pair):
    """Return the two input values in opposite order."""
    a, b = pair
    a = b
    b = a
    return [a,b]
```

```text
exchange([2,9])
AssertionError: expected [9, 2], observed [9, 9]
```

**Base** — 3/3 behavioral checks; cause 2/2, explanation 1/2.

`````text
```json
{
  "category": "AssertionError",
  "root_cause": "The code is trying to swap the elements of the list by assigning `b` to `a`, but then it assigns `a` back to `b`. This results in both variables being set to the same value, which is why the assertion fails.",
  "corrected_code": "def exchange(pair):\n    \"\"\"Return the two input values in opposite order.\"\"\"\n    a, b = pair\n    a, b = b, a\n    return [a,b]",
  "explanation": "The correct way to swap the elements of a list is to assign the second element to the first and vice versa. The corrected code uses this approach."
}
```
`````

**Adapter** — 3/3 behavioral checks; cause 0/2, explanation 1/2.

`````text
{"category": "WrongResult", "root_cause": "The expression 'b' at that location is used where an assignment is required.", "corrected_code": "def exchange(pair):\n    \"\"\"Return the two input values in opposite order.\"\"\"\n    a, b = pair\n    a, b = b, a\n    return [a,b]", "explanation": "Use 'b, a' at that operation to restore the intended assignment."}
`````

Review: A explains the overwritten value but its rationale does not explain simultaneous assignment. B's tuple hint is relevant, but its cause and repair instructions are incomplete.

## suffix-mass

Slicing the unit suffix leaves strings which cannot be accumulated by numeric sum.

```python
def total_kg(labels):
    """Sum integer masses written as a number followed by kg."""
    return sum(label[:-2] for label in labels)
```

```text
total_kg(['2kg','12kg'])
TypeError: unsupported operand type(s) for +: 'int' and 'str'
```

**Base** — 3/3 behavioral checks; cause 1/2, explanation 2/2.

`````text
```json
{
  "category": "TypeError",
  "root_cause": "The `+` operator cannot be used to add an integer and a string.",
  "corrected_code": "def total_kg(labels):\n    \"\"\"Sum integer masses written as a number followed by kg.\"\"\"\n    return sum(int(label[:-2]) for label in labels)",
  "explanation": "In the original code, `label[:-2]` is a string that needs to be converted to an integer before it can be added to another integer. The `int()` function is used to convert the string to an integer, which allows the `+` operator to work correctly."
}
```
`````

**Adapter** — 3/3 behavioral checks; cause 0/2, explanation 1/2.

`````text
{"category": "TypeError", "root_cause": "The expression 'label[:-2]' yields an integer where a string is required.", "corrected_code": "def total_kg(labels):\n    \"\"\"Sum integer masses written as a number followed by kg.\"\"\"\n    return sum(int(label[:-2]) for label in labels)", "explanation": "Use 'int(label[:-2])' at that operation to restore the intended conversion."}
`````

Review: A describes the symptom, then correctly links sliced text to conversion before summing. B reverses the types in its cause but names the cast.

## metadata-items

The values view is not a mapping and has no items method.

```python
def attributes(record):
    """Return sorted field names with a non-None value."""
    return sorted(k for k,v in record.values().items() if v is not None)
```

```text
attributes({'q':0,'a':None})
AttributeError: 'dict_values' object has no attribute 'items'
```

**Base** — 3/3 behavioral checks; cause 1/2, explanation 2/2.

`````text
```json
{
  "category": "AttributeError",
  "root_cause": "The `values()` method of a dictionary returns an iterator over the values of the dictionary, not a list of tuples.",
  "corrected_code": "def attributes(record):\n    \"\"\"Return sorted field names with a non-None value.\"\"\"\n    return sorted(k for k,v in record.items() if v is not None)",
  "explanation": "The `items()` method should be used instead of `values()` to get both keys and values from the dictionary. The `items()` method returns a view object that displays a list of a dictionary's key-value tuple pairs."
}
```
`````

**Adapter** — 3/3 behavioral checks; cause 2/2, explanation 1/2.

`````text
{"category": "AttributeError", "root_cause": "The expression 'record.values().items()' accesses the items of the values view instead of the key-value pairs.", "corrected_code": "def attributes(record):\n    \"\"\"Return sorted field names with a non-None value.\"\"\"\n    return sorted(k for k,v in record.items() if v is not None)", "explanation": "Use 'record.items()' at that operation to restore the intended access."}
`````

Review: A locates the invalid values-view access and gives a terse replacement. B calls the view an iterator but explains how items supplies keys and values.

## rfind-missing

The missing marker gives -1, which as a slice stop drops the final character.

```python
def before_last(text, mark):
    """Keep all text when the marker is absent; otherwise return the prefix before its last occurrence."""
    i = text.rfind(mark)
    return text[:i]
```

```text
before_last('abc','!')
AssertionError: expected 'abc', observed 'ab'
```

**Base** — 3/3 behavioral checks; cause 1/2, explanation 2/2.

`````text
```json
{
  "category": "AssertionError",
  "root_cause": "The rfind method returns -1 if the substring is not found in the string.",
  "corrected_code": "def before_last(text, mark):\n    \"\"\"Keep all text when the marker is absent; otherwise return the prefix before its last occurrence.\"\"\"\n    i = text.rfind(mark)\n    if i == -1:\n        return text\n    else:\n        return text[:i]",
  "explanation": "The original code incorrectly returned 'ab' instead of 'abc' because it did not check if the marker was present in the text. The rfind method returns -1 if the substring is not found, so we need to add an additional condition to handle this case."
}
```
`````

**Adapter** — 2/3 behavioral checks; cause 0/2, explanation 0/2.

`````text
{"category": "WrongResult", "root_cause": "The expression 'text.rfind(mark)' returns the index of the first match instead of the last.", "corrected_code": "def before_last(text, mark):\n    \"\"\"Keep all text when the marker is absent; otherwise return the prefix before its last occurrence.\"\"\"\n    i = text.rindex(mark)\n    return text[:i]", "explanation": "Use 'text.rindex(mark)' at that operation to restore the intended behavior."}
`````

Failed inputs and expected values

```text
before_last('abc','!') -> 'abc'
```

Review: A mischaracterizes rfind and proposes rindex, which raises on absence. B identifies the missing sentinel and explains guarding the missing marker, though its cause omits negative slice semantics.
