**No substantiated security findings in the reviewed scope.**

Using the installed security-audit skill, I reviewed `pricing.py`, `test_pricing.py`, and the supplied `BASE/pricing.py` → `HEAD/pricing.py` diff. No immutable revision was provided. The change replaces the `$` display prefix with `USD `; input validation and formatting arithmetic remain unchanged.

Ran `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest -v`: **2 tests passed; exit code 0.** The tests confirmed the supplied whole/fractional formatting examples and rejection of the tested invalid inputs.

This establishes the observed behavior for those cases. The review did not cover callers, upstream authorization, transaction processing, or deployment, and does not establish application-wide security. No dependencies were installed, network used, unrelated files inspected, or source files edited.
