"""Small calculator fixture for controlled repository-operator benchmarks."""


def median(values: list[float]) -> float:
    """Return the median of a non-empty sequence of numeric values."""
    if not values:
        raise ValueError("median requires at least one value")
    ordered = sorted(values)
    middle = len(ordered) // 2
    return float(ordered[middle])
