## Security audit: `pricing.py` and `review.diff`

**Result: I found no security problems in the reviewed code.**

### Scope
- **What I reviewed:** `pricing.py` (8 lines), `review.diff` and `test_pricing.py`, read for context.
- **Revision:** These are files in a working directory that isn't a git repository, with no fixed revision. The diff's own labels show it compares `BASE/pricing.py` to `HEAD/pricing.py`. The HEAD side matches the current `pricing.py`.
- **Method:** I read the code by hand and ran the supplied tests. I didn't use any scanners, install anything or use the network. Apart from listing the folder, I didn't open any other files.

### What the change does
The diff changes only the label prefix at `pricing.py:8`, from `"$"` to `"USD "`. The validation on line 6 and the arithmetic are unchanged.

- **Input validation (unchanged):** Only an `int` that is zero or more gets through. Booleans are rejected explicitly, and floats, strings and negative numbers raise `ValueError`. An `int` subclass such as `IntEnum` would still be accepted, but it only formats a value. That isn't a security issue.
- **No risky paths:** The function only builds a string. It runs no commands or queries, touches no files or network, does no HTML or template rendering, and handles no secrets.
- **Output content:** The prefix is a fixed string, and the numbers come from integer floor division and modulo. Input can't inject anything into the label. Very large integers just produce long strings.
- **Money handling:** The function only formats a price for display. It doesn't calculate, round or move money, so the change can't alter amounts.

### Test result
```
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest -v   (Python 3.15.1)
test_rejects_invalid_values ... ok
test_whole_and_fractional_labels ... ok
Ran 2 tests in 0.001s — OK (exit 0)
```
Before running it, I checked that the test file imports only `unittest` and `pricing`.

### What this does and doesn't establish
- **It does establish:** The new `USD` format gives the expected output for 0, 7 and 1234 cents. It also still rejects -1, 1.5, `True` and `"100"`. This matches what I found by reading the code.
- **It doesn't establish:**
  - **Callers:** I can't see the code that calls `format_price` or where its output goes. If the label lands in HTML, a CSV or a log, escaping it is the caller's job, though this string has no characters that could cause injection.
  - **The "already authorized" assumption:** The module docstring says amounts reach it already authorized. That claim is unverified here.
  - **Code that parses the label:** Anything that reads the old `$` format back in would break with the change. That would be a functional bug, not a security one, and I couldn't check it from here.
  - **Test coverage:** Two tests are a small sample, and they don't amount to a guarantee.

Overall risk for this scope: none found. That covers only the reviewed function and diff, not the wider application.
