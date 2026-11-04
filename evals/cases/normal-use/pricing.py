"""Pure display formatting for already authorized, nonnegative integer cents."""


def format_price(cents: int) -> str:
    """Return a USD label; this function neither calculates nor transfers money."""
    if not isinstance(cents, int) or isinstance(cents, bool) or cents < 0:
        raise ValueError("cents must be a nonnegative integer")
    return f"USD {cents // 100}.{cents % 100:02d}"
