## Security audit: `pricing.py` and `review.diff`

**Result: No substantiated security findings in the reviewed scope.**

### Scope
- **What I reviewed:** `pricing.py` and `review.diff`, with `test_pricing.py` for context. This folder isn't a git repository, so there's no fixed revision. The base and head versions are the ones `review.diff` labels `BASE/pricing.py` and `HEAD/pricing.py`. The working-tree `pricing.py` matches the HEAD side.
- **Method:** I read the code and ran the supplied tests locally. I didn't install anything, use the network, open other files or edit anything.

### What the change does
The diff changes one line, `pricing.py:8`. The label prefix goes from `$` to `USD ` (for example, `$12.34` becomes `USD 12.34`). The input check on line 6 is the same in base and head:
- it accepts only `int` values;
- it rejects `bool` values, which Python would otherwise treat as integers;
- it rejects negative numbers.

### Security analysis
- **Untrusted input:** the only input is `cents`, and the check above stops floats, strings, booleans and negative values before formatting. The output contains only the fixed prefix and digits that the code computes, so no attacker-controlled text can reach it.
- **Money handling:** the docstring says the function "neither calculates nor transfers money," and the code agrees: it performs no state change, I/O or transfer. The module docstring says the cents are "already authorized." That authorization happens in callers that weren't supplied, so this review doesn't check it.
- **Injection or output encoding:** the string contains only `USD`, a space, digits and a period, so it's safe to put into HTML, SQL or shell text. Any risk would depend on how a caller uses the string, and no callers were supplied.
- **New issues in the diff:** none. The change affects only the label's appearance. It doesn't touch validation or arithmetic.
- **Not a security issue:** very large integers make longer strings, but nothing supplied shows a way to abuse that. A caller that expects the old `$` format would be a compatibility concern, not a vulnerability.

### Test result
```
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest -v
test_rejects_invalid_values ... ok
test_whole_and_fractional_labels ... ok
Ran 2 tests in 0.000s — OK (exit 0)
```

**What the tests show:**
- The new `USD` format is correct for 0, 7 and 1234 cents.
- The function raises `ValueError` for `-1`, `1.5`, `True` and `"100"`.

**What the tests don't show:** the tests run only the function itself, not any caller. So they don't cover:
- the upstream authorization the docstring relies on;
- how callers use or encode the label;
- other integer-like types such as `numpy.int64`, which the check would reject because they aren't Python `int`;
- any deployment behaviour.

### Coverage and limits
I looked at input validation, injection and output risk, and whether the change could affect money calculations. I didn't review callers, the code that supplies the authorized cents, or how labels are displayed, because none of it was supplied. The overall risk applies only to this one function and its diff. This result reflects only these two files and isn't a security guarantee for the wider application.
