import pytest
from calculator import median


def test_median_odd_length() -> None:
    assert median([3, 1, 2]) == 2.0


def test_median_even_length() -> None:
    assert median([1, 2, 3, 4]) == 2.5


def test_median_rejects_empty_input() -> None:
    with pytest.raises(ValueError):
        median([])
