Test file only imports pricing and unittest; safe to run.

I found no security problems in `pricing.py` or the change in `review.diff`, and both supplied tests passed.

## Scope
- **What I reviewed:** `pricing.py` (working-tree copy; there's no git history here, so no fixed revision to cite) and `review.diff`, which compares BASE and HEAD of `pricing.py`. I read `test_pricing.py` for context.
- **What the change does:** it edits one line, `pricing.py:8`. The price label changes from `$12.34` to `USD 12.34`. The input check on line 6 is the same before and after.
- **How I checked:** I read the code by hand and ran the supplied tests on this machine. I installed nothing, used no network, opened no other files and edited nothing.

## Test result
`PYTHONDONTWRITEBYTECODE=1 python3 -m unittest -v` (Python 3.15.1):
- `test_whole_and_fractional_labels` passed
- `test_rejects_invalid_values` passed
- 2 tests ran in 0.001s, result OK, exit code 0.

Before running the tests I checked that the test file only imports `unittest` and `pricing`.

## Findings
**No substantiated security findings in the reviewed scope.**

- `format_price` only formats a number. It reads no files, makes no network calls, runs no commands and touches no stored data. Its docstring says it "neither calculates nor transfers money."
- Line 6 rejects anything that isn't a whole number of cents, including `True`/`False` and negative numbers. Since only whole numbers get through, the output is always `USD`, digits, a dot and two digits. Nothing a caller passes in can add other text to the label.
- The diff changes only the fixed `$` / `USD ` prefix, so it adds no new way to attack the code.

## What the review and tests establish
**They show:**
- The function returns the expected labels for 0, 7 and 1234 cents.
- It rejects `-1`, `1.5`, `True` and `"100"`.
- By reading the code, the output can only contain the characters listed above.

**They don't show:**
- **Callers:** the module says it handles "already authorized, nonnegative integer cents", but whether the amounts were really authorized is up to the calling code, which wasn't supplied. I didn't assume either way.
- **Where the label is shown:** how it's displayed or escaped in HTML, logs or anything else wasn't supplied. The label itself has no characters that would need escaping, though.
- **Effects on other code:** nothing supplied shows whether other code parses or compares the old `$` format. That would be a compatibility question, not a security one, and I didn't check it.
- **Other edge cases:** the tests don't cover very large numbers or subclasses of `int`. Reading the code, these still can only produce digits.
- **Overall risk:** I'm not rating the wider application, because this review only covered one small function.

No follow-up is needed for this scope.
