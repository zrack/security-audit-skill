## Security audit: `pricing.py` / `review.diff`

**Result: no security problems found in the reviewed files.** That covers only these files; it isn't a guarantee that the code or the application using it is secure.

### Scope
- **What I reviewed:** `pricing.py` (the current working-tree file), `review.diff` (BASE → HEAD, one hunk in `pricing.py`), and `test_pricing.py` for context. This isn't a git repository, so there is no commit to pin the review to; it reflects the files on disk at review time.
- **How:** I read the code and ran the supplied tests locally. I didn't install anything, use the network, edit files, or open any other files in the folder.

### The change
In `review.diff`, the output prefix changes from `"$"` to `"USD "`. Nothing else changes:
- The input check stays the same (`pricing.py:6`). It still rejects anything that isn't a plain integer, including `True`/`False`, and negative numbers.
- The function only builds a text label from fixed text and two integers (`pricing.py:8`). Callers can't get their own text into the output, and it does no lookups, file or network access, or money handling.

Nothing in the change passes outside input into a command, query, page or file, and there are no credentials.

### Test result
Command: `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest -v` (Python 3.15.1)
```
test_rejects_invalid_values ... ok
test_whole_and_fractional_labels ... ok
Ran 2 tests in 0.000s
OK   (exit 0)
```
Before running it, I checked that the test file only imports `unittest` and `pricing`.

### What this does and doesn't show
- **Shows:** the new `"USD "` format comes out right for 0, 7 and 1234 cents. The function raises `ValueError` for `-1`, `1.5`, `True` and `"100"`.
- **Doesn't show:**
  - Whether every caller really passes amounts that are already approved and non-negative, as the module docstring assumes. I didn't see any callers.
  - Whether anything downstream depended on the old `"$"` format. That would be a compatibility issue, not a security one.
  - How the label is shown on screen. It has no characters that are risky in HTML, but I didn't look at how it gets rendered.
  - Behaviour with very large integers or integer subclasses. The tests don't cover these, and neither crosses a trust boundary I could see.

**Overall risk for this scope:** low. The function has no inputs that cross a trust boundary, and the change only alters a fixed text prefix.
