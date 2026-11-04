## Security audit: `pricing.py` and `review.diff`

**Result: no substantiated security findings in the reviewed scope.** The review found no security problems. That isn't a guarantee the code is secure.

### Scope
- **Reviewed:** `pricing.py`, `review.diff`, and `test_pricing.py` for context. This folder isn't a git repository, so there is no fixed revision. The diff's `BASE/pricing.py` → `HEAD/pricing.py` labels are taken as given. The current file matches the diff's HEAD side.
- **The change:** a single line, `pricing.py:8`. The output prefix goes from `$` to `USD `. Input validation and the arithmetic are the same before and after.
- **Method:** I read the code by hand and ran the supplied tests. No scanners, dependency installs, network access or other files were used.

### Test result
I ran `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest -v` with Python 3.15.1:
```
test_rejects_invalid_values ... ok
test_whole_and_fractional_labels ... ok
Ran 2 tests in 0.000s
OK   (exit 0)
```

### What the review and tests establish
- `format_price` only builds a string. It does no I/O, uses no shell, SQL or templates, and makes no network calls. It doesn't change any state.
- Validation (`pricing.py:6`) rejects anything that isn't an integer, rejects `bool`, and rejects negative values. The tests confirm this for `-1`, `1.5`, `True` and `"100"`.
- Formatting is correct for 0, 7 and 1234 cents. The diff introduces no new security-relevant behaviour; only the text of the label changes.

### What they don't establish
- **Authorization isn't done here.** The module docstring (`pricing.py:1`) describes the input as "already authorized, nonnegative integer cents." That is a requirement on the caller, not a check inside this function. The function also says it "neither calculates nor transfers money." I had no callers to check, so I can't say whether any caller actually authorizes the amount first.
- **Output context wasn't reviewed.** The output only contains `USD`, digits and a dot, so it isn't an injection risk by itself. Where the label ends up (HTML, PDFs, logs) is outside this scope.
- **Not tested:** `int` subclasses other than `bool` (they are accepted), very large integers, and how downstream code handles the new `USD ` prefix in place of `$`. That last one is a compatibility question, not a security one.
- **Coverage:** two tests is a narrow suite. Passing them shows that the formatting cases and the rejected inputs listed above behave as expected, nothing more.

No overall risk rating is given for the application, because only this one function was in scope.
